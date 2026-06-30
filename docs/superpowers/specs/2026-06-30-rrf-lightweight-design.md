# RRF 轻量融合 — 设计文档

## 背景

当前 `search_raw()` 在 Query Rewrite 开启时，会生成多条子查询并分别检索，然后通过 `seen` set 简单去重合并。这种方式丢失了各子查询的排名信息。

## 目标

在 QR 的子查询结果之间引入 Reciprocal Rank Fusion（RRF）融合，让"多条子查询共识"的文档排在前面，提升检索召回质量。

## 范围

- **新文件**: `src/retrieval/rrf.py` — RRF 融合函数
- **改文件**: `src/tools/impl/rag_tool.py` — `search_raw()` 中去重合并段替换为 RRF 融合
- **无需配置开关**: RRF 随 QR 自动生效，QR 关闭时只有 1 条子查询，RRF 自然不生效

## 设计

### rrf_fuse 函数

```python
def rrf_fuse(
    ranked_lists: list[list[tuple[str, dict]]],
    k_constant: int = 60,
    top_k: int = 10,
) -> tuple[list[str], list[dict]]:
```

- 输入：N 条子查询的结果列表，每条列表的元素为 `(doc_text, metadata)` 元组
- 输出：RRF 融合后 Top-K 条文档及其 metadata
- 排名从 1 开始，文档按 `(source, chunk_index)` 去重后累加 RRF 得分
- k_constant = 60（RRF 论文经典值）

### search_raw 改动

```python
# 改动前：
#   for sq in sub_queries: dedup by seen → all_docs
# 改动后：
ranked_lists = []
for sq in sub_queries:
    r = vs.similarity_search(query=sq, k=recall_k)
    docs_batch = r["documents"][0] if r.get("documents") else []
    metas_batch = r["metas"][0] if r.get("metadatas") else [None] * len(docs_batch)
    ranked_lists.append(list(zip(docs_batch, metas_batch)))

if len(ranked_lists) > 1:
    all_docs, all_metas = rrf_fuse(ranked_lists, top_k=recall_k)
else:
    all_docs, all_metas = ranked_lists[0]
```

### 数据流

```
Query → QR → [sq1, sq2, sq3]
               │      │      │
         VectorSearch VectorSearch VectorSearch
               │      │      │
         [(d, m)]  [(d, m)]  [(d, m)]
               └──────┼──────┘
                  RRF Fuse
                      │
              [(d1, m1), (d2, m2), ...]  ← 融合后排序
                      │
                  Reranker  → Top-K 输出
```

## 测试

- 单条列表 → 原样返回
- 两条相同列表 → 排序不变
- 三条列表，文档 A 在 3 条中都排第 1 → A 应显著高于其他
- 三种空列表组合 → 正常处理
- k_constant = 1 的极端情况 → 不崩溃
