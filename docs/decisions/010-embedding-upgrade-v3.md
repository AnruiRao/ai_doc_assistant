# 010: Embedding 模型升级（V3 评测驱动）

- **日期**: 2026-06-26
- **状态**: 计划中

## 背景

决策 001 在 V1 阶段选用了 `paraphrase-multilingual-MiniLM-L12-v2`（384 维），并计划在 V3 通过评测对比 MiniLM vs BGE vs API-based 的检索效果。

V3 评测（RAGAS baseline F=0.38, R=0.82）暴露了检索质量的瓶颈。虽然 chunk 碎片化是低分主因，但 embedding 模型的中文语义匹配能力是基础层限制。20 条 query 中有多条（#3 Agent run 参数、#14 RAG Tool 方法、#19 异常体系）检索到的 chunk 完全无关，embedding 质量不足是诱因之一。

## 选项对比

| 模型 | 维度 | 中文效果 | 部署 | 加载耗时 | 推荐场景 |
|------|------|---------|------|---------|---------|
| `paraphrase-multilingual-MiniLM-L12-v2`（当前） | 384 | 中等 | 本地 | ~2s | 已有，作为 baseline |
| **`BAAI/bge-base-zh-v1.5`** | 768 | 好 | 本地 | ~5s | **推荐**：免费 + 中文优化 + 社区成熟 |
| `BAAI/bge-small-zh-v1.5` | 512 | 好 | 本地 | ~3s | 备选：轻量版，精度略低但更快 |
| `shibing624/text2vec-base-chinese` | 768 | 好 | 本地 | ~5s | 备选：中文专用，社区广泛使用 |
| 千问 text-embedding-v3 | — | 优 | API | 有网络延迟 | 付费（DashScope），效果最优但依赖网络 |

## 决策

**V3 阶段选择 `BAAI/bge-base-zh-v1.5`**，理由：

1. **中文最优（免费本地模型）**：BGE 在 C-MTEB 中文榜单上排名靠前，768 维比 MiniLM 384 维承载更多语义信息
2. **零额外成本**：本地运行，免费
3. **社区成熟**：BGE 是 BAAI（北京智源）出品，中文 RAG 社区广泛使用
4. **直接替换**：与当前 MiniLM 同为 SentenceTransformer 格式，`VectorStore` 只需改一行模型名
5. **加载时间可接受**：~5s 首加载（`./run.sh` 启动时完成一次），不影响运行时

### 放弃的理由

- **API embedding**（千问/OA）：V3 阶段仍希望本地运行，不引入网络依赖和 API 成本
- **bge-small**：512 维比 384 维提升有限，选 base 版（768 维）边际效益更高
- **text2vec**：效果接近 BGE，但 BGE 社区更大、更新更活跃

## 架构改动

当前 Chroma auto-embed 模式（`get_or_create_collection` 传 `embedding_function`），切换模型只需改构造函数参数：

```python
# 当前
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
# 改为
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-base-zh-v1.5"
)
```

**重要**：切换模型后**必须重索引全部文档**，因为新旧模型生成的向量空间不兼容，旧向量与新查询无法可比对。

## 后续计划

1. 先在 `VectorStore` 替换模型名
2. 删除旧 Chroma 数据（`rm -rf data/chroma`）
3. 用 `rag_tool save` 重索引全部项目文档
4. 重跑 RAGAS 评估对比分数
5. 若效果未达预期，考虑候选方案（bge-small / text2vec）

## 参考

- [BGE on HuggingFace](https://huggingface.co/BAAI/bge-base-zh-v1.5)
- [C-MTEB 中文排行榜](https://github.com/FlagOpen/FlagEmbedding/tree/master/FlagEmbedding/baai_general_embedding)
- 原决策：[001-embedding-model.md](001-embedding-model.md)
