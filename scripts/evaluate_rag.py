#!/usr/bin/env python3
"""
RAGAS 评估脚本 — 跑 20 条测试 query，出 faithfulness + answer_relevancy baseline。

用法:
  uv run python scripts/evaluate_rag.py

输出:
  - data/eval_raw.json         原始数据（query + answer + contexts）
  - data/eval_scores.json      RAGAS 评分（summary + per-query）
"""

import json
import os
import sys
import time
from pathlib import Path

# 确保 src 可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# RAGAS 0.4.x
from ragas.metrics.collections.faithfulness.metric import Faithfulness
from ragas.metrics.collections.answer_relevancy.metric import AnswerRelevancy

from core.config import Settings
from core.llm import BaseLLM
from tools.registry import ToolRegistry
from tools.impl.rag_tool import RagTool
from agents.react_agent import ReactAgent


def parse_queries(md_path: str) -> list[str]:
    """从 test-queries.md 提取 query 文本列表。"""
    queries = []
    with open(md_path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "---" in line or "Query" in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                num = parts[1].strip()
                if num.isdigit():
                    queries.append(parts[2])
    return queries


def main():
    start_total = time.time()
    output_dir = Path(__file__).resolve().parent.parent / "data"

    # ---- 加载测试 query ----
    md_path = Path(__file__).resolve().parent.parent / "docs" / "test-queries.md"
    queries = parse_queries(str(md_path))
    print(f"📋 加载了 {len(queries)} 条测试 query\n")

    # ---- 收集数据（若已有原始数据则跳过） ----
    raw_path = output_dir / "eval_raw.json"
    config = Settings.from_env()
    config.temperature = 0.0  # 评测需要确定性，覆盖为 0
    if raw_path.exists():
        print("💡 已有原始数据，跳过 Agent 调用阶段\n")
        with open(raw_path) as f:
            raw_data = json.load(f)
        questions = [d["question"] for d in raw_data]
        answers = [d["answer"] for d in raw_data]
        contexts = [d["contexts"] for d in raw_data]
    else:
        # ---- 初始化 Agent ----
        llm = BaseLLM(config=config)
        registry = ToolRegistry()
        rag_tool = RagTool()
        registry.register_tool(rag_tool)
        agent = ReactAgent(llm=llm, tool_registry=registry, max_steps=15)
        print("🤖 Agent 初始化完成\n")

        questions, answers, contexts = [], [], []
        for i, q in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] Query: {q[:50]}...")
            start = time.time()

            # 获取 Agent 回答（内部通过 rag_tool.search 走 rewrite）
            answer = agent.run(q, history=[])

            # 获取检索上下文：复用 rag_tool.search_raw，与 Agent 内部检索一致
            docs, _ = rag_tool.search_raw(query=q, k=4)

            questions.append(q)
            answers.append(answer)
            contexts.append(docs)

            elapsed = time.time() - start
            print(f"  → 回答 {len(answer)} 字, {len(docs)} 条上下文, 耗时 {elapsed:.1f}s\n")

        # ---- 保存原始数据 ----
        output_dir.mkdir(exist_ok=True)
        with open(raw_path, "w") as f:
            json.dump(
                [
                    {"question": q, "answer": a, "contexts": c}
                    for q, a, c in zip(questions, answers, contexts)
                ],
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"💾 原始数据已保存到 {raw_path}")

    # ---- RAGAS 评估（支持断点续评）----
    print("⚙️ 运行 RAGAS 评估（LLM-as-judge）...\n")

    import asyncio
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory

    # Judge: LLM 评分 — 用 RAGAS 的 llm_factory 包装 AsyncOpenAI client
    judge_llm = llm_factory(
        config.model,
        client=AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        ),
        temperature=0,
        max_tokens=int(os.getenv("RAGAS_MAX_TOKENS", "32768")),
        extra_body={"thinking": {"type": "disabled"}},
    )

    # Embedding: 单独渠道（支持与 Judge 不同平台）
    embed_client = AsyncOpenAI(
        api_key=os.getenv("EMBEDDING_API_KEY", config.api_key),
        base_url=os.getenv("EMBEDDING_BASE_URL", config.base_url),
    )
    from ragas.embeddings.openai_provider import OpenAIEmbeddings as RagasOpenAIEmbeddings

    faithfulness = Faithfulness(llm=judge_llm)
    answer_relevancy = AnswerRelevancy(
        llm=judge_llm,
        embeddings=RagasOpenAIEmbeddings(client=embed_client, model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3")),
    )

    # 断点续评：加载已有评分，已有则跳过
    scores_path = output_dir / "eval_scores.json"
    existing_map = {}
    if scores_path.exists():
        existing = json.load(scores_path.open())
        existing_map = {e["query"]: e for e in existing["per_query"]}
        done = sum(1 for q in questions if q in existing_map and existing_map[q]["faithfulness"] is not None)
        print(f"💡 已有 {done}/{len(questions)} 条评分，{len(questions)-done} 条待重评\n")

    # 用 None 占位，确保索引对齐
    faith_scores: list[float | None] = [None] * len(questions)
    relevancy_scores: list[float | None] = [None] * len(questions)
    for i, q in enumerate(questions):
        if q in existing_map:
            faith_scores[i] = existing_map[q]["faithfulness"]
            relevancy_scores[i] = existing_map[q]["answer_relevancy"]

    async def score_all():
        for i, (q, a, ctx) in enumerate(zip(questions, answers, contexts)):
            if faith_scores[i] is not None:
                continue  # 已评分，跳过

            print(f"  评分 [{i + 1}/{len(questions)}]...", end=" ", flush=True)
            try:
                fs = await faithfulness.ascore(
                    user_input=q, response=a, retrieved_contexts=ctx
                )
                faith_scores[i] = fs.value
                print(f"faith={fs.value:.3f}", end=" ")
            except Exception as e:
                # 留 None 不赋值，后续跳过逻辑靠 is not None 判断，不会误跳
                print(f"faith=ERR({e})", end=" ")
            try:
                rs = await answer_relevancy.ascore(user_input=q, response=a)
                relevancy_scores[i] = rs.value
                print(f"relevancy={rs.value:.3f}")
            except Exception as e:
                print(f"relevancy=ERR({e})")

    asyncio.run(score_all())

    # ---- 输出结果 ----
    import pandas as pd

    df = pd.DataFrame({
        "query": questions,
        "faithfulness": faith_scores,
        "answer_relevancy": relevancy_scores,
    })

    # ── 只对有效分数求平均 ──
    valid_faith = [s for s in faith_scores if s is not None]
    valid_relev = [s for s in relevancy_scores if s is not None]
    print("\n" + "=" * 60)
    print("📊 RAGAS 评估结果")
    print("=" * 60)
    print(f"\n有效评分 Faithfulness:     {len(valid_faith)}/{len(questions)} 条")
    if valid_faith:
        print(f"平均 Faithfulness:     {sum(valid_faith)/len(valid_faith):.3f}")
    print(f"有效评分 Answer Relevancy: {len(valid_relev)}/{len(questions)} 条")
    if valid_relev:
        print(f"平均 Answer Relevancy: {sum(valid_relev)/len(valid_relev):.3f}")
    print()

    # 保存评分（None 写为 null，后续加载后 None is not 已评分，会重试）
    scores_path = output_dir / "eval_scores.json"
    scores_data = {
        "summary": {
            "faithfulness": round(sum(valid_faith)/len(valid_faith), 4) if valid_faith else None,
            "answer_relevancy": round(sum(valid_relev)/len(valid_relev), 4) if valid_relev else None,
        },
        "per_query": [
            {
                "query": row["query"],
                "faithfulness": row["faithfulness"],
                "answer_relevancy": row["answer_relevancy"],
            }
            for _, row in df.iterrows()
        ],
    }
    with open(scores_path, "w") as f:
        json.dump(scores_data, f, ensure_ascii=False, indent=2)
    print(f"💾 详细分数已保存到 {scores_path}")

    elapsed = time.time() - start_total
    print(f"\n⏱️ 总计耗时: {elapsed:.0f}s")
    print("✅ 评估完成")


if __name__ == "__main__":
    main()
