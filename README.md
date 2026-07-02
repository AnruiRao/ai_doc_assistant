<p align="center">
  <h1 align="center">市场监管办事导办助手</h1>
  <p align="center">基于自实现 RAG + ReAct Agent 的政务办事导办系统，核心链路零依赖框架</p>
</p>

<p align="center">
  <a href="https://github.com/AnruiRao/ai_doc_assistant"><img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python" alt="Python"></a>
  <a href="https://github.com/AnruiRao/ai_doc_assistant/actions"><img src="https://img.shields.io/badge/passing-94%20tests-brightgreen?logo=github" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="docs/test-queries.md"><img src="https://img.shields.io/badge/RAGAS_Faithfulness-0.79-brightgreen" alt="RAGAS F=0.79"></a>
  <a href="https://github.com/AnruiRao/ai_doc_assistant/blob/main/docs/decisions/"><img src="https://img.shields.io/badge/arch_decision-13%20records-blueviolet" alt="13 decisions"></a>
</p>

---

## 🎯 亮点

- **自实现 ReAct** — 手写 while + tool_calls 循环，非 LangChain 封装
- **自实现 RAG** — loader → cleaner → chunker → VectorStore，全链路可控
- **评测驱动优化** — Faithfulness 从 0.38 提升至 **0.79**（+108%）
- **BGE 中文语义** — bge-base-zh-v1.5 + Reranker 精排，中文检索优化
- **政务文档解析** — 章节识别（编号+命名章节）+ 政务网页抓取，垂直领域就绪
- **13 条架构决策记录** — 每条记录"为什么这样选"，面试可直接引用

## 🚀 快速开始

```bash
# 30 秒启动
git clone https://github.com/AnruiRao/ai_doc_assistant.git && cd ai_doc_assistant
cp .env.example .env         # 填入你的 LLM_API_KEY
uv sync && ./run.sh          # FastAPI + Streamlit 一键启动
```

```bash
# 或只用 API
uv run uvicorn src.api.main:app --reload
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"input_text":"办理个体户营业执照需要哪些材料？","history":[]}'
```

## 📸 截图

> 截图待补充。

## ✨ 功能

| 功能 | 一句话描述 |
|------|------------|
| 📄 文档上传 | `.txt` / `.pdf` 自动清洗、切分、向量化 |
| 🌐 网址导入 | 粘贴政务公开网页 URL，自动抓取、解析、入库 |
| 🔍 语义检索 | Chroma + BGE 向量 + 滑动窗口上下文 |
| 🏷️ 政务章节识别 | 自动标记办事指南的"申请条件/办理材料/办理流程"章节 |
| 🤖 ReAct Agent | 思考 → 调工具 → 观察 → 回答，纯手写循环（市场监管领域 prompt） |
| 🛠️ 工具系统 | 可扩展 Tool 基类 + Registry，支持 RAG/计算器等 |
| 🌐 REST API | FastAPI 异步路由，OpenAI 兼容协议 + URL 导入接口 |
| 🖥️ Streamlit UI | 瘦客户端，纯 httpx 调后端，零后端依赖 |
| 📊 RAGAS 评测 | 20 条测试 query，Faithfulness + Relevancy 双指标 |
| 📝 决策记录 | 13 条架构决策，每个都写明了权衡和放弃的理由 |

## 🏗️ 架构

```
用户 → Streamlit UI ──HTTP──→ FastAPI ──→ ReAct Agent
                                            │
                                  ToolRegistry ──→ RAG Tool ──→ Chroma + BGE
                                            │
                                       BaseLLM (OpenAI 兼容)
```

**全链路自实现**：Agent 循环、Tool 系统、RAG Pipeline（加载 → 清洗 → 切分 → 向量化 → 检索），核心代码不依赖 LangChain / LlamaIndex。每个环节可独立修改和调试。

## 📊 评测

### 优化历程

| 轮次 | 改动 | Faithfulness |
|------|------|:------------:|
| Baseline | chunk_size=500, overlap=50, MiniLM | 0.38 |
| +chunk/滑动窗口等 | 多轮目测调优 | 逐项改善 |
| +BGE embedding | 升级 bge-base-zh-v1.5 | **0.6353** (+67%) |
| +GLM 重评 | 切换 GLM-4.5-Air 全量重评 | 0.68 |
| **+Reranker 精排** | **cross-encoder 重排序** | **0.7883** (+16%) ✅ |

**最新分数（Reranker 开，GLM-4.5-Air）**

| 指标 | Baseline | +Reranker |
|------|:--------:|:---------:|
| Faithfulness | 0.6788 | **0.7883** (+16.1%) |
| Answer Relevancy | 0.8619 | 0.8664 (+0.5%) |

> 评测脚本 [`scripts/evaluate_rag.py`](scripts/evaluate_rag.py)，评分数据 [`data/eval_scores.json`](data/eval_scores.json)。

## 🧭 进化路线

| 阶段 | 状态 |
|------|------|
| **V1 Demo** — Agent + RAG + UI 全链路跑通 | ✅ 完成 |
| **V2 工程化** — FastAPI/异步桥接/服务层/测试+CI | ✅ 完成 |
| **V3 RAG 优化** — Reranker 精排（F=0.68→0.79） | ✅ 收敛 |
| **垂直领域 Phase A** — 市场监管办事导办，章节识别 + 网页导入 + 领域 prompt | ✅ 完成 |
| **V4 异步改造** — AsyncOpenAI + 流式输出 | 🔲 规划中 |
| **V4 生产化** — Docker / 多用户 / LangChain 适配 | 🔲 规划中 |

## 📁 项目结构

```
src/
├── core/          LLM 封装、Agent 基类、配置、异常、重试、日志
├── tools/         Tool 基类 + Registry + RAG 工具/计算器
├── agents/        ReAct Agent 实现（市场监管领域 prompt）
├── ingestion/     文档加载、清洗、递归切分 + 短段合并 + 政务章节识别 + 网页抓取
├── retrieval/     Chroma 向量库 + BGE Embedding + Reranker
├── services/      文档管理服务层
├── api/           FastAPI 路由（chat / health / documents / ingest-url）
└── app/           Streamlit 界面（瘦客户端 + URL 导入）
```

> 完整目录详见 [`PLAN.md`](PLAN.md)。

## 📖 决策记录

每个架构决策都记录了选项对比、权衡分析和放弃的理由

- [001: Embedding 模型选型](docs/decisions/001-embedding-model.md)
- [002: ReAct VS Plan&Execute](docs/decisions/002-react-vs-plan-execute.md)
- [003: Tool 系统设计](docs/decisions/003-tool-system-design.md)
- [004: Agent 多轮对话设计方案](docs/decisions/004-agent-conversation-design.md)
- [005: RAG Tool 设计](docs/decisions/005-rag-tool-design.md)
- [006: V2 异常体系设计](docs/decisions/006-v2-exception-hierarchy.md)
- [007: FastAPI + 异步桥接方案](docs/decisions/007-fastapi-async-bridge.md)
- [008: V3 滑动窗口上下文](docs/decisions/008-sliding-window-context.md)
- [009: Chunker 短段落合并](docs/decisions/009-chunk-fragmentation-merge.md)
- [010: Embedding 升级 BGE](docs/decisions/010-embedding-upgrade-v3.md)
- [011: Query Rewrite](docs/decisions/011-query-rewrite.md)
- [012: Reranker 选型](docs/decisions/012-reranker-selection.md)
- [013: RRF 轻量融合](docs/decisions/013-rrf-lightweight.md)

## 🛠️ 技术栈

| 层 | 选型 |
|----|------|
| Agent 框架 | 自实现 ReAct（零框架依赖） |
| RAG Pipeline | 自实现（loader → cleaner → chunker → search） |
| 向量库 | Chroma + BGE (768d) |
| LLM 协议 | OpenAI 兼容（支持千问 / DeepSeek / GLM） |
| 后端 | FastAPI + structlog |
| 前端 | Streamlit（瘦客户端） |
| 测试 | pytest + GitHub Actions（94 用例） |
| 包管理 | uv |

## 📜 License

MIT License. See [LICENSE](LICENSE).

---

<p align="center">
  <a href="PLAN.md">📋 项目规划</a> · <a href="TASKS.md">✅ 任务清单</a> · <a href="docs/decisions/">📝 决策记录</a>
</p>
