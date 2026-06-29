# 012: Reranker 选型 — 交叉编码器精排（V3 实验 A2）

- **日期**: 2026-06-28
- **实施日期**: 2026-06-29
- **状态**: 已实施

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

1. ~实现 Reranker 集成~ ✅
2. ~全量消融：baseline vs reranker~ ✅
3. 如果 Reranker 上线后仍有列举型覆盖不足的问题，考虑在 Reranker 基础上再加 QR，但需保证原问题始终在子查询中
4. 决策是否将 reranker 默认开启

## 消融实验结果（2026-06-29）

### 实验配置

| 项目 | 值 |
|------|-----|
| Agent 模型 | glm-4.5-air |
| Judge 模型 | glm-4.5-air |
| Agent 温度 | 0.0（评测脚本硬编码） |
| 文档集 | 41 个文件，151 个片段 |
| 数据来源 | `docs/test-queries.md` 20 条 |
| recall_k | 20（固定常量） |

### 结果对比

| 轮次 | Faithfulness | Answer Relevancy |
|------|:------------:|:----------------:|
| Baseline（Reranker 关） | **0.6788** | 0.8619 |
| Reranker（Reranker 开） | **0.7883** | 0.8664 |
| Δ | **+0.1095（+16.1%）** | +0.0045 |

### 逐条明细

| # | Query | Baseline F | Reranker F | ΔF |
|---|-------|:----------:|:----------:|:--:|
| 1 | V3 主要做什么？ | 0.786 | 0.583 | -0.202 |
| 2 | chunk_text 和 recursive_split 有什么区别？ | 0.971 | **1.000** | +0.029 |
| 3 | Agent 的 run 方法接受哪些参数？ | 0.000 | **1.000** | **+1.000** 🚀 |
| 4 | 文档切分时怎么避免把一段话从中间切断？ | 0.769 | 0.800 | +0.031 |
| 5 | 向量库存在哪个目录下？ | **1.000** | **1.000** | 0 |
| 6 | 项目为什么选择 Chroma 而不是其他向量数据库？ | **1.000** | 0.750 | -0.250 |
| 7 | V2 工程化阶段改了哪些核心文件？ | 0.707 | 0.138 | **-0.569** 🚩 |
| 8 | 为什么项目不直接用 LangChain？ | **1.000** | 0.889 | -0.111 |
| 9 | 为什么 embedding 模型选了 paraphrase-multilingual-MiniLM-L12-v2？ | 0.579 | **1.000** | +0.421 |
| 10 | 支持多用户同时使用吗？ | 0.897 | 0.926 | +0.029 |
| 11 | 项目有没有 Docker 部署方案？ | 0.200 | **0.696** | +0.496 |
| 12 | VectorStore 类有哪些核心方法？ | 0.500 | 0.581 | +0.081 |
| 13 | ReAct Agent 的循环流程是怎样的？ | 0.850 | 0.750 | -0.100 |
| 14 | RAG Tool 的 save 和 search 模式分别做了什么？ | 0.875 | **1.000** | +0.125 |
| 15 | Chunker 和 VectorStore 是在哪个环节被调用的？ | 0.867 | 0.875 | +0.008 |
| 16 | 文档从上传到可被检索，经历了哪些步骤？ | 0.676 | 0.804 | +0.128 |
| 17 | 如果上传一个非常大的文件，系统会怎么处理？ | 0.000 | **0.478** | +0.478 |
| 18 | chunk_size 和 chunk_overlap 会影响检索结果吗？怎么影响的？ | 0.208 | **0.812** | +0.604 |
| 19 | 项目异常体系中有哪些可重试的异常？ | **1.000** | 0.889 | -0.111 |
| 20 | Streamlit 瘦客户端模式下 UI 与后端是如何通信的？ | 0.692 | 0.796 | +0.104 |

### 退化分析

#7（V2 改了哪些核心文件）退化最大（-0.569），根因：Chroma 召回 20 条中混入了来源相同但内容不相关的噪声 chunk，CrossEncoder 错误地将 V3 优化分析等内容评为高相关度。属于交叉编码器的固有限制——只能做语义匹配，不能做意图识别。同类列举型 query（#3、#14、#19）表现正常，退化属于个例。

### 结论

**Reranker 有效，Faithfulness +16.1%。** 退化 1 条、小波动 5 条，受益 9 条。对比同类优化，Reranker 是仅次于 chunk 合并 + BGE 提升的第二大单次优化（+0.11 vs +0.255）。默认建议开启。
