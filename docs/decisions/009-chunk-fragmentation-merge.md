# 009: Chunker 短段落合并策略

- **日期**: 2026-06-26
- **状态**: 已完成
- **实现**: `src/ingestion/chunker.py` `_merge_short_chunks()` 方法

## 背景

V2 实现的 `recursive_split` 按 `\n\n`（段落）→ `\n`（行）→ 字符层级切分，但短段落（如标题、列表项）直接被放入独立 chunk：

```python
for paragraph in text.split("\n\n"):
    if len(paragraph) <= chunk_size:
        chunks.append(paragraph)  # ← 标题/短行直接独立成块
        continue
```

RAGAS 评估发现，大量 chunk 是 15-30 字符的标题碎片（如 `"## 第五阶段：V3 实测驱动 + RAG 优化级"`），检索命中标题但带不回具体内容，导致 Faithfulness 仅 0.38。

## 问题分析

20 条 query 中，Faithfulness < 0.2 的 6 条均受碎片化影响：

| Query | F | 上下文特征 |
|-------|---|-----------|
| ReAct 循环流程 | 0.083 | 只有"需要选择 Agent 模式"等空标题 |
| 异常体系可重试 | 0.091 | 只有"Phase 1 已完成"标题行 |
| Docker 方案 | 0.176 | Plan 信息零散在多个小 chunk 中 |

滑动窗口（前后各 2 个相邻 chunk）已被证明有效（#11、#16 从 ⚠️→✅），但滑动窗口只能补齐同源短序列，无法根本解决"标题和正文不在同一批次 chunk"的问题。

## 选项对比

| 方案 | 复杂度 | 效果预期 | 副作用 |
|------|--------|---------|--------|
| A: 阈值合并 | ★ 在 `recursive_split` 加合并逻辑 | 中——消除短碎片 | 可能把不相关内容合入同一块 |
| B: Markdown 结构分组 | ★★ 解析标题层级，按章节分组 | 高——语义完整 | 仅对 Markdown 文档有效 |
| C: 语义分割 | ★★★ 用 embedding 检测话题边界 | 高 | 依赖额外模型，慢 |
| D: 纯增大 chunk_size | ★ 一个参数 | 低——已有 chunk_size=1000 | 短行仍独立，只是更少 |

## 决策

**选择方案 A（阈值合并）作为短期修复，方案 B（Markdown 结构分组）作为 V3 增强目标。**

### 阈值合并规则

```
1. 遍历段落列表，累计长度
2. 当前累计 < min_chunk 时，继续追加下个段落
3. 当前累计 >= min_chunk 时，出一个 chunk，重置累计
4. 末尾不足 min_chunk 的段落合并到最后一个 chunk
```

参数：`min_chunk = chunk_size * 0.4`（即 chunk_size=1000 时，最短 chunk 400 字符）

### 为什么不是方案 B

Markdown 结构分组精确度高，但需要判断文档类型（纯文本/代码/Markdown），复杂度超出 V3 阶段目标。V3 的核心是"用实测驱动，一次只改一个变量"，阈值合并改动最小、效果最可归因。

## 后续计划

- **V3 当前**：在 `recursive_split` 内实现阈值合并逻辑
- **V3 后续**：重索引文档 → 重跑 RAGAS 验证
- **V4（可选）**：按 Markdown 标题结构分组 + metadata 增强（记录章节路径）

## 参考

- Chroma 官方 chunking 建议：推荐至少 200 token 保底
- LangChain RecursiveCharacterTextSplitter 的 `length_function` 可自定义度量
- Pinecone 博客："Chunking Strategies for RAG"
