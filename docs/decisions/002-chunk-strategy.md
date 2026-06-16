# 002: 文本分块策略

- **日期**: 2026-06-17
- **状态**: 已实施（V1 固定切分），V2 计划扩展

## 背景

文档需要切分成片段才能存入向量库。分块策略直接影响检索精度。

## 当前实现

`Chunker` 类（`src/ingestion/chunker.py`）使用固定字符数切分 + 重叠：

- chunk_size=500, chunk_overlap=50
- 游标法：`while start < len(text)` → `end = start + chunk_size` → `start = end - overlap`
- 校验：`chunk_overlap >= chunk_size` 抛异常

## 选项对比

| 策略 | 优点 | 缺点 | 适用场景 |
|---|---|---|---|
| 固定字符切分 | 简单、确定性强、容易调试 | 可能切断语义完整的段落 | V1 验证阶段 |
| 递归字符分割 | 按段落/句子边界切，语义更完整 | 实现略复杂 | 大部分通用文档 |
| 语义分割 | 按话题边界切，上下文最完整 | 需要额外模型，慢 | 长文档、书籍 |
| 文档结构分割 | 按 Markdown 标题/PDF 章节切 | 依赖文档格式 | 结构化文档 |

## 决策

**V1 使用固定字符切分**，原因：

1. **可预测**：每块大小固定，调试时容易定位问题
2. **零依赖**：纯字符串操作，不需要额外的 NLP 模型
3. **足够验证**：V1 目标是全链路跑通，不是最优检索精度

## 后续计划

- **V2**：实现递归字符分割（参考 LangChain `RecursiveCharacterTextSplitter` 的思路），配置化切换策略

## 参考

- LangChain RecursiveCharacterTextSplitter 源码
- "Chunking Strategies for RAG" (Pinecone blog)
