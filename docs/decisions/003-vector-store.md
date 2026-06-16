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
5. **学习成本低**：面试场景下，Chroma 是"至少听过"的入门方案

### 放弃 FAISS 的理由

FAISS 需要手动管理 id 映射和增删操作，V1 阶段不想处理这些细节。

### 放弃 Milvus/Weaviate 的理由

V1 项目不需要分布式向量库。后续如果项目规模增长（百万级文档），才需要考虑。

## 后续计划

- **V2**：支持配置化切换向量库后端，Chroma 为默认，预留 FAISS 选项
- **V3**：如果有评测需要对比不同向量库的检索效果

## 参考

- [Chroma 文档](https://docs.trychroma.com/)
