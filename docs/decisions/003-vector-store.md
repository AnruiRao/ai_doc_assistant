# 003: 向量库选型

- **日期**: 2026-06-17
- **状态**: 已实施

## 背景

需要向量数据库存储文档片段的 embeddings，支持语义检索。

## 选项

| 方案 | 部署方式 | 规模上限 | 学习成本 |
|---|---|---|---|
| Chroma | 本地(PersistentClient) | 小 | 低 |
| FAISS | 本地(内存/文件) | 中 | 中 |
| Milvus | 服务端 | 大 | 高 |
| Weaviate | 服务端 | 大 | 高 |

## 决策

**选用 Chroma PersistentClient**，理由：

1. **零配置**：不需要启动服务端，Python 直接调用
2. **本地持久化**：`PersistentClient` 数据存本地磁盘，重启不丢失
3. **内置 embedding**：auto-embed 简化 V1 流程，不用手动管理 embedding 调用
4. **API 简洁**：基本操作（add / query / count / delete）几行代码搞定
5. **学习成本低**：Chroma 是入门门槛最低的方案

### 放弃 FAISS 的理由

FAISS 需要手动管理 id 映射和增删操作，V1 阶段不想处理这些细节。

### 放弃 Milvus/Weaviate 的理由

V1 项目不需要分布式向量库。后续如果项目规模增长（百万级文档），才需要考虑。

## 后续计划

- **V1**：Chroma PersistentClient + auto-embed（`paraphrase-multilingual-MiniLM-L12-v2`）
- **V2**：Chromaa 保持，重点在 FastAPI 工程化（异常体系、服务层、异步桥接），向量库不变
- **V3**：Chroma 保持，但 embedding 从 MiniLM 切换到 bge-base-zh-v1.5（见决策 010），auto-embed 改为手动模式
- **V4（可选）**：支持配置化切换向量库后端，预留 FAISS 选项，或对比不同向量库的检索效果

## 参考

- [Chroma 文档](https://docs.trychroma.com/)
