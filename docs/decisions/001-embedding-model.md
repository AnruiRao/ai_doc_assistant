# 001: Embedding 模型选型

- **日期**: 2026-06-17
- **状态**: 已实施（V1），计划 V3 重新评估

## 背景

RAG pipeline 需要将文本转为向量，用于语义检索。项目面向中文技术文档，需要选择 embedding 模型。

## 选项

| 模型 | 维度 | 中文效果 | 成本 | 部署方式 |
|---|---|---|---|---|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 中等 | 免费 | 本地 |
| BGE (bge-base-zh-v1.5) | 768 | 好 | 免费 | 本地 |
| OpenAI text-embedding-3-small | 1536 | 好 | 付费 ($0.02/1K tokens) | API |

## 决策

**V1 阶段选用 `paraphrase-multilingual-MiniLM-L12-v2`**，理由：

1. **零成本**：V1 阶段验证可行性，不需要为 embedding 付费
2. **本地运行**：SentenceTransformer 直接加载，不需要网络请求
3. **多语言支持**：模型名含 multilingual，中文检索可用
4. **轻量**：384 维 + MiniLM 架构，CPU 推理速度快

### 放弃 BGE 的理由（V1）

BGE 中文效果更好，但 V1 阶段不需要最优精度，需要的是最快跑通。BGE 留到 V3 评测阶段对比。

### 放弃 OpenAI 的理由（V1）

付费 + 网络依赖 + 数据外传。V1 本地优先。

## 后续计划

- **V3**：引入评测 QA 集，量化对比 MiniLM vs BGE vs API-based embedding
- **V2-V3**：将 embedding 从 Chroma auto-embed 改为手动模式，支持替换

## 参考

- [SentenceTransformer 模型列表](https://www.sbert.net/docs/pretrained_models.html)
- [BGE on HuggingFace](https://huggingface.co/BAAI/bge-base-zh-v1.5)
