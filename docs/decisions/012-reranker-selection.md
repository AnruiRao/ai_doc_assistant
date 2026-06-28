# 012: Reranker 选型 — 交叉编码器精排（V3 实验 A2）

- **日期**: 2026-06-28
- **状态**: 计划中

## 背景

[V3 实验 A1 Query Rewrite](011-query-rewrite.md) 的消融实验暴露了两个问题：

1. **精度瓶颈**：Embedding 模型（bge-multilingual-gemma2）做粗召回，top-4 中混入不相关内容的概率随文档量增长
2. **QR 净收益低**：仅 +0.017 Faithfulness，但引入流程/事实型问题的退化

Reranker 的核心思路是**不改变召回面，只提升排序精度**：

```
粗召回 k=20  (embedding，快召宽进)
    ↓
精排取 top-4 (reranker 交叉编码，按相关性排序)
    ↓
传给 LLM
```

相比 QR，Reranker 的优势是**对所有问题类型一致受益**，没有"拆碎了导致视角丢失"的副作用。

## 候选方案

### 方案一：BAAI/bge-reranker-v2-m3（推荐）

| 属性 | 值 |
|------|-----|
| 模型大小 | ~500MB |
| 最大长度 | 1024 tokens |
| 语言 | 多语言（中英等） |
| 推理速度 | CPU ~150ms / 对 |
| 依赖 | sentence-transformers（已有） |

**优势**：
1. 与现有 embedding 模型同属 BAAI 生态，使用体验一致
2. 多语言支持好，覆盖项目中/英文文档
3. SentenceTransformer CrossEncoder 接口，零额外依赖
4. 模型大小适中，笔记本可跑

**劣势**：
1. 1024 token 上限对超长 doc 需要截断
2. CPU 推理比纯向量搜索慢 10-20 倍（但 k=20 规模下可接受）

### 方案二：BAAI/bge-reranker-v2-gemma

| 属性 | 值 |
|------|-----|
| 模型大小 | ~2.2GB |
| 最大长度 | 8192 tokens |
| 语言 | 多语言 |
| 推理速度 | CPU ~800ms / 对 |

**优势**：
1. Gemma 2B 做基座，精度最高
2. 8192 超长上下文，无需截断

**劣势**：
1. 体积大、速度慢，不适合实时搜索
2. 当前项目文档 chunk 最长 ~1000 tokens，1024 上限够用

### 方案三：maidalun1020/bce-reranker-base_v1

| 属性 | 值 |
|------|-----|
| 模型大小 | ~400MB |
| 最大长度 | 512 tokens |
| 语言 | 中文为主 |

**优势**：
1. 中文重度优化
2. 体积略小

**劣势**：
1. 英文支持弱于 bge
2. 512 tokens 上限偏紧，可能截断较长 chunk

### 方案四：cross-encoder/ms-marco-MiniLM-L-6-v2

| 属性 | 值 |
|------|-----|
| 模型大小 | ~80MB |
| 最大长度 | 512 tokens |
| 语言 | 仅英文 |

**劣势**：
1. 纯英文模型，不适合中文文档
2. 精度偏低

## 决策

**选择 BAAI/bge-reranker-v2-m3**，理由：

1. **零新依赖，最小的集成成本**：项目已依赖 `sentence-transformers`，`CrossEncoder` 原生支持，无额外包
2. **精度满足需求**：作为交叉编码器，即使 max_length=1024，精度也远超 embedding 级相似度
3. **与 embedding 模型同生态**：同为 BAAI 出品，部署、缓存路径统一
4. **资源消耗可接受**：CPU ~150ms/对，20 对 ≈ 3s，在 Agent 的 `asyncio.to_thread` 中不阻塞主流程
5. **扩展性**：后续可换 bge-reranker-v2-gemma 做精度验证，接口完全兼容

### 放弃的理由

- **bge-reranker-v2-gemma**：当前文档 chunk（~1000 tokens）不需要 8192 上限，2.2GB 部署成本高
- **bce-reranker-base_v1**：512 token 上限偏紧，且英文文档支持弱
- **MiniLM**：纯英文，不适合本项目

## 架构改动

### 修改文件

| 文件 | 改动 |
|------|------|
| `src/core/config.py` | 加 `enable_reranker: bool` 开关，默认 `False` |
| `src/retrieval/reranker.py` | **新增**，Reranker 封装：懒加载 CrossEncoder + `rerank()` 方法 |
| `src/tools/impl/rag_tool.py` | `search_raw()` 中：enable_reranker=True → k=20 → rerank → top-4 |

### Reranker 接口设计

```python
class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self._model = None  # 懒加载

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 4,
    ) -> list[tuple[str, float]]:
        """
        交叉编码重排：
          1. 拼接 (query, doc) 对
          2. CrossEncoder 逐对打分
          3. 按分数降序排列
          4. 返回 top_k (doc, score) 列表
        """
```

### 关键设计决策

1. **懒加载**：`CrossEncoder` 在首次调用 `rerank()` 时初始化，启动不加载模型
2. **k 值联动**：启用 Reranker 时 `search_raw` 内部 `k=20` 粗召回 → rerank → 取 top-4；关闭时仍用 `k=4`
3. **同步封装**：`rerank()` 是同步方法，通过 `asyncio.to_thread` 在 Agent 线程池中运行
4. **分数透传**：rerank 分数只用于排序，不传给 LLM，LLM 只看到最终选出的 top-4 文档内容
5. **设备自适应**：`device='mps'`（Mac Metal）或 `'cpu'` 自动检测

## 后续计划

1. 实现 Reranker 集成
2. 全量消融：baseline vs reranker vs reranker+qr
3. 对比 reranker 和 qr 的精度/耗时/覆盖度
4. 如果 V3 优化收敛（连续 2-3 轮改进后肉眼无法感知提升），关闭 RAG 优化阶段，进入 V4 生产化阶段
5. 决策是否将 reranker 默认开启
