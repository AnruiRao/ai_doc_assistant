# AI 文档助手 — 项目规划

## 快速定位（30 秒了解）

### 这是什么？
RAG + 自实现 ReAct Agent 的智能文档问答系统。从 Demo 逐步演进到生产级产品。

### 现在在哪？
- ✅ **V1 完成** — Agent 核心 + RAG 检索 + Streamlit UI 全链路跑通
- ✅ **V2 完成** — 异常体系、FastAPI、服务层、测试 CI、Streamlit 瘦客户端
- 🟡 **V3 收敛中** — Reranker 精排（F=0.68→0.79，默认开）；QR+RRF（已实现，单一检索策略无收益，默认关）
- 🔲 **V3.5 异步改造 + 流式** — LLM→Agent→API 全链路 async（AsyncOpenAI），砍掉 to_thread 桥接
- 🔲 **方向调整** — 从通用文档问答转向垂直领域（待明确方向）

### 快速上手
```bash
cp .env.example .env && uv sync
./run.sh                                    # 一键启动（FastAPI + Streamlit）
uv run pytest tests/ -v                     # 跑测试
```

### 代码速览
```
src/ingestion/  文档加载+切分+清理     src/retrieval/  向量库 (Chroma)
src/agents/     ReAct 循环             src/tools/      工具系统
src/api/        FastAPI 路由           src/app/        Streamlit UI
docs/decisions/ 架构决策记录
```

### 想看什么？
- 架构 → `src/core/agent.py`
- 加 Tool → 继承 `src/tools/base.py` 的 `Tool`
- 改 RAG → `src/retrieval/vector_store.py` 或 `src/ingestion/chunker.py`
- 决策 → `docs/decisions/`

---

## 项目定位

一个带 RAG 能力的 AI Agent 助手，作为大模型应用开发的学习项目，逐步靠近生产级产品。

> 规划转向垂直领域（待明确方向），计划将项目从通用文档问答调整为特定领域的知识库系统。

## 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.12+ | LLM 生态首选 |
| API 协议 | OpenAI 兼容 | 通用生态，岗位最多 |
| LLM SDK | OpenAI Python SDK | 直接对接，透明可控 |
| Agent | 自实现 ReAct | 核心亮点 |
| RAG pipeline | 自实现 | 核心亮点 |
| 向量库 | Chroma | 本地运行，零配置 |
| 文档解析 | pypdf | 轻量 |
| 前端 | Streamlit | 最快出界面 |
| 包管理 | uv | 现代、快 |

### 框架策略（核心决策）

**V1-V3：核心逻辑自实现**（ReAct、RAG pipeline），不依赖 LangChain/LlamaIndex。

理由：
- 自己实现一遍才能真正理解底层原理，而不仅是 API 调用
- 自己能控制 prompt、tool_calls 流程，调试更容易
- LangChain 迭代快，API 不稳定，学它不如学底层原理

**V4 之后：引入 LangChain 适配层**，做对比实现。

具体做法：在 `src/vendor/` 下加适配器，将自实现模块与 LangChain 组件做对比，或直接在部分链路替换为 LangChain。这样既展现原理深度，又证明框架迁移能力。

### 国产模型

使用千问（DashScope），兼容 OpenAI API 格式。

---

## 架构分层

```
core/           ← 核心抽象：配置、LLM 封装、Agent 基类、异常
tools/          ← 工具系统：Tool 基类、ToolRegistry 注册器
ingestion/      ← 文档处理：加载、切分
retrieval/      ← 向量检索：embedding、Chroma 封装
agents/         ← 具体 Agent 实现：ReActAgent
app/            ← 前端界面：Streamlit
```

设计原则：`core` + `tools` 是抽象层，下层模块具体实现，上层 `app` 组装。

### 实际代码特点（V1 已完成部分）

- **ABC 抽象基类**：`Agent`、`Tool` 均使用 ABC，子类必须实现 `run()`
- **Pydantic 配置**：`Settings` 使用 Pydantic BaseModel + `from_env()` 工厂方法
- **双 invoke 方法**：`BaseLLM.invoke()` 返回内容字符串，`invoke_with_tools()` 返回完整消息对象（含 tool_calls）
- **异常体系**：独立 `exceptions.py`，后续可扩展具体异常子类
- **Chunking 游标法**：`chunk_text()` 用 `while start < len(text)` + 游标回溯实现重叠切片
- **Chroma auto-embed**：当前用 Chroma 内置 embedding（auto-embed），写/查穿同一函数避免配错
- **多语言 embedding**：使用 `paraphrase-multilingual-MiniLM-L12-v2`，中文检索可用
- **Tool input model 设计**：多模式工具（save/search）用 Field description 标签区分，`use_for` 为唯一必填，LLM 只传需要的字段
- **Tool run 返回值**：统一返回字符串（而非原始 dict），Agent 循环直接消费，不需要额外序列化
- **17 个 pytest 用例**：loader 7 + chunker 6 + vector_store 4

```
src/
├── core/               ← 抽象层
│   ├── config.py       #   Pydantic BaseModel + from_env()
│   ├── llm.py          #   OpenAI SDK 封装（invoke + invoke_with_tools）
│   ├── agent.py        #   Agent ABC 基类
│   └── exceptions.py   #   异常基类
├── tools/              ← 工具抽象层
│   ├── base.py         #   Tool ABC 基类
│   ├── registry.py     #   ToolRegistry 注册器
│   └── impl/
│       ├── calculator.py  #  计算器工具
│       └── rag_tool.py    #  RAG 知识库工具（save + search）
├── agents/             ← 具体 Agent
│   └── react_agent.py  #   ReAct 循环实现
├── ingestion/          ← 文档处理
│   ├── loader.py       #   load_text / load_pdf / load_document
│   └── chunker.py      #   Chunker（chunk_size + chunk_overlap）
├── retrieval/          ← 向量检索
│   └── vector_store.py #   Chroma 封装（add / search / count / delete）
└── app/                ← （待实现）
```

---

## 进化路线

### V1 — Demo 级（目标周期：2 周）

功能：
- 配置管理 + LLM 调用封装
- 工具系统（Tool 基类 + Registry）
- ReAct Agent 循环
- 基础文档切分 + Chroma 存储
- 简单 RAG 检索
- Streamlit 界面（上传文档 + 对话）

验收：上传文档 → 检索 → Agent 回答，全链路跑通

### V2 — 工程化级

**核心路径（按顺序做完即可验收）**

**Phase 1：基础设施 ✅ 已完成**
- 更新依赖（fastapi、uvicorn、httpx、tenacity、structlog）
- 异常体系树形化（`AssistantBaseError` → LLMError/AgentError/RetrievalError...）
- tenacity 重试（指数退避，区分可重试 vs 不可重试）
- structlog 结构化日志

**Phase 2：基础 RAG 改进（能力优先）**
- ✅ ~~文本噪声清理（空行压缩、特殊字符过滤）~~
- ✅ ~~递归分割（优先段落边界切分，而非固定字符）~~
- ✅ ~~集成到 rag_tool save 流程~~
- 不引入新依赖，一个函数解决问题

**Phase 3：FastAPI + 异步桥接 ✅ 已完成**
- FastAPI 路由（`POST /chat`、`GET /health`）
- App 工厂模式 + 异常→HTTP 状态码映射
- `asyncio.to_thread()` 调 sync Agent，不做 AsyncBaseLLM/AsyncAgent

**Phase 4：E2E 验证 + 文档更新 ✅ 已完成**
- 全链路验证（FastAPI + Streamlit 双进程）
- README 更新、决策记录补充

**增强路径（核心路径完成后，时间充裕再回补）**

已完成的增强：
- ✅ **Streamlit 瘦客户端**：全走 httpx 调 FastAPI，剔除 Agent/Chroma 依赖，`./run.sh` 一键启动
- ✅ **文档管理 API**：`POST /upload`、`GET /documents`、`DELETE /documents/{id}` + JSON 注册表

待回补：
- **服务层**：DocumentService、AgentService、ChatService
- **测试 + CI**：Mock 测试、pytest-asyncio、GitHub Actions

> **V2 → V3 承上启下**：V2 的 FastAPI 作为实验调用入口，Process agent 层为 RAG 实验提供接口。V3 的实测优化直接复用这套架构。

详细实施计划见 `.claude/plans/scalable-honking-popcorn.md`。

### V3 — 实测驱动 + RAG 优化级 ✅ 实验收敛

**核心方法：问题驱动，而不是指标驱动**

V3 的流程是循环式的：

```
实际使用 → 记下回答不好的问题（15-20个）
    ↓
分析最突出的短板（召回差？幻觉？切分不合理？）
    ↓
做一次针对性改动（只改一个变量）
    ↓
用同样的问题重跑，肉眼对比改善
    ↓
重复
```

**实验结论：**

| 实验 | Faithfulness | 对比 Baseline | 开关 |
|---|---|---|---|
| Baseline | 0.6788 | — | 全关 |
| Reranker 精排 | **0.7883 (+16%)** | 🏆 有效，默认开 | `ENABLE_RERANKER=true` |
| QR only | 0.7202 | 有效但 Reranker 更优 | — |
| QR+RRF+Reranker | 0.6692 | 单一检索策略下无收益 | `ENABLE_QUERY_REWRITE=false` |

**RRF 结论**：RRF 需要多种异构检索策略才有价值（如向量 + BM25），当前仅有一种检索方式，RRF 融合多条近似子查询无实际收益。代码已实现并保留，为未来 Hybrid Search 预留。

**为什么这么做？**
- 标注 50-100 条 QA 数据的成本被严重低估（实际 5-8 小时纯人工）
- 大多数 RAG 问题的瓶颈只有 1-2 个，不需要全面评测就能找到
- 自动评测 pipeline 在优化稳定前是过度工程化

**可能涉及的方向（依实际瓶颈而定，一次只改一个变量）**

每次改前先用"同一批问题跑两遍"确认效果，有效保留、无效回退。

### 可选操作清单

**A. 检索质量**

| 操作 | 解决问题 | 复杂度 |
|------|---------|--------|
| 换 embedding 模型（bge / text-embedding-3） | 语义理解不够好 | ★ 一行配置 |
| 加 reranker（cross-encoder / bge-reranker） | 检索结果前几名不相关 | ★★ 新增一个类 |
| Hybrid search（向量 + BM25） | 精确关键词匹配不到 | ★★★ 新增检索路径 |
| 显式 cosine similarity 控制 | 距离度量不明确 | ★ 数值计算 |

**B. 查询优化**

| 操作 | 解决问题 | 复杂度 |
|------|---------|--------|
| Query rewrite（LLM 改写用户问题） | 用户问得模糊 | ★ 一个 prompt |
| Multi-query（多问法扩展后合并结果） | 单一问法覆盖不全 | ★★ 多路查询 |
| HyDE（先生成假答案，再用假答案检索） | query-chunk 语义 gap 大 | ★★ 生成+检索两阶段 |

**C. 文档预处理**

| 操作 | 解决问题 | 复杂度 |
|------|---------|--------|
| 文档去重（内容哈希 ID） | 重复文档污染检索 | ★ ID 策略替换 |
| Metadata 增强（标题/章节路径解析） | 检索结果缺少上下文 | ★★ 依赖文档结构解析 |
| MMR 去冗余 | top-k 结果太相似 | ★★ 一个算法函数 |
| Sliding window context（返回相邻 chunk） | 单 chunk 信息不全 | ★ 返回时扩展 |

**D. 策略调参**

| 操作 | 解决问题 | 复杂度 |
|------|---------|--------|
| top-k 调优（5→10→20） | top-k 太小漏结果 | ★ 一个参数 |
| chunk_size 对比实验 | chunk 太大/太小 | ★ 一个参数 |
| 分割策略对比（固定 vs 递归） | chunk 边界切断语义 | ★ 换函数名 |

> 不预设优化顺序。每一次改动只用"同一批问题跑两遍"来验证效果。当连续 2-3 轮改动后肉眼已无法感知改善（瓶颈收敛），再考虑是否需要建正式评测集做定量分析。

### V4 — 异步改造 + 生产化级（规划中）

- **全链路异步化**：`OpenAI` → `AsyncOpenAI`，砍掉 `asyncio.to_thread` 桥接，Agent→LLM→API 全在事件循环
- **流式输出**：LLM stream() + Agent async generator + FastAPI StreamingResponse + Streamlit 流式渲染
- Docker + docker-compose 部署
- 多用户 + Session 管理
- 缓存（Redis）
- API 鉴权 + 速率限制
- 异步文档处理队列
- `@tool` 装饰器：在 `src/tools/` 下自实现 `@tool` 装饰器，展示语法糖与基类继承的对比
- LangChain 适配器：在 `src/vendor/` 下加入 LangChain 对比实现或适配层

### V5 — 深度进阶级（可选，偏研究探索）

- 知识图谱 RAG / GraphRAG
- 多模态（代码截图、图表识别）
- 模型路由（简单问题用小模型）
- Prompt 注入防护
- 成本追踪

> V5 内容为探索性方向，非必须实现。GraphRAG 属于结构化知识 + 图推理的技术栈跃迁，V4 之后根据实际需求评估是否值得投入。

---

## 当前进度

**V1 Demo 阶段已全部完成** ✅ — Agent 核心 + RAG 检索 + Streamlit UI + 全链路验证。

**V2 工程化级 ✅ 已完成**
- Phase 1（基础设施：异常、重试、日志）✅
- Phase 2（RAG 基础优化：噪声清理、递归分割、集成到 rag_tool）✅
- Phase 3（FastAPI + 异步桥接）✅
- Phase 4（E2E 验证 + 文档更新）✅
- 增强：文档管理 API（上传/列表/删除）✅
- 增强：Streamlit 瘦客户端（全走 httpx，剔除 Chroma 依赖）✅
- 增强：一键启动 `./run.sh` ✅
- **增强**：服务层（DocumentService + routes 变薄 + rag_tool 去重）✅
- **增强**：测试 + CI（41 测试 + GitHub Actions）✅

**V3 实测驱动 + RAG 优化 ✅ 实验收敛**
- [x] Phase 1：收集 20 条测试 query（`docs/test-queries.md`）
- [x] 第 1 轮：chunk_size 500→1000，overlap 50→100（#1 ❌→✅）
- [x] 第 2 轮：Agent 搜索次数代码硬拦截 max_search=3（避免无限循环）
- [x] 第 3 轮：滑动窗口上下文，命中 chunk 带回前后各 2 个相邻 chunk（#11、#16 ⚠️→✅）
- [x] RAGAS 评估 pipeline 搭建（scripts/evaluate_rag.py，支持断点续评）
- [x] Phase 2：RAGAS 评估补全，出完整 baseline（F=0.38, R=0.82, 20/20 条）
- [x] Phase 3-1：chunker 短段落合并（决策 009 已完成）
- [x] Phase 3-2：embedding 模型切换 BAAI/bge-base-zh-v1.5（决策 010 已完成）
- [x] Phase 4：重索引 + 重评测（F=0.6353, R=0.8819, ↑67%）
- [x] Phase 5：证据落地到 docs/decisions/ 和 test-queries.md
- [x] **实验 A2：Reranker 集成**（决策 012，F=0.679→0.788，+16.1%，默认开）
- [x] **实验 A1：QR + RRF 完整实现**（决策 011 + 013，已实现但单一检索策略下 F=0.669 无收益，默认关，为 Hybrid Search 预留）

---

### embedding 策略设计决策

当前使用 Chroma **auto-embedding**（`paraphrase-multilingual-MiniLM-L12-v2`），写入和查询用同一个 embedding 函数，保证向量空间一致。

未来演进方向（V2-V3）：
- 替换为 API-based embedding（千问 `text-embedding-v3` / OpenAI `text-embedding-3-small`）→ 转为手动方式
- 调用方新增 `EmbeddingModel` 类，`VectorStore.add/search` 加可选 `embeddings` 参数
- auto-embed 与手动方式二选一，不共存耦合

---

### RAG Tool ID 策略设计决策

RAG Tool 的核心问题是：**多次保存文档时如何避免 Chroma 的 ID 碰撞（upsert 覆盖）？** 每阶段策略不同，随项目演进逐步完善。

| 阶段 | ID 策略 | 方案说明 | 优点 | 缺点 |
|---|---|---|---|---|
| **V1 Demo** | UUID | 每次 save 生成 uuid4()，metadata 记 source 追溯来源 | 无碰撞风险，一行搞定 | ID 不可读，重复上传产生副本 |
| **V2 工程化** | UUID + 同名替换 | 每次 save 用 uuid4()，上传前按 filename 匹配删旧文档 | 无碰撞，零配置，同名文件自动替换 | ID 不可读，重复上传不产生副本 |
| **V3 评测驱动** | 内容哈希 | MD5(chunk) 做 ID，内容不变 ID 不变 | 确定性、可复现评测、自动去重 | 哈希碰撞理论风险极低 |
| **V4 生产化** | 文件名+序号+用户ID | 拼接 user123_doc.txt_0 | 多用户天然隔离 | ID 变长 |

**V2 当前实现要点**：
- `ids = [str(uuid4()) for _ in chunks]` — 永远不碰撞
- `metadatas` 存 `{"source": path, "chunk_index": i}` — 搜索结果可显示来源
- search 返回 `[来源: xxx]` 标签 — Agent 能告知用户信息出处
- delete 模式支持按 `source` 参数删除指定文档或清空全库
- list 模式读取注册表 `data/documents.json` 返回文档列表
- 同名上传自动替换：先删旧文档（Chroma + 磁盘 + 注册表）再存新文档
- 无相关性阈值 — V1 直接 top-k 返回，V3 引入距离阈值

---

# 对话背景

## 为什么会做这个项目

正在学习大模型应用开发，需要通过一个项目来：
1. 边学边练，把学到的知识落地
2. 从简单开始，逐步迭代到接近生产水平的系统

## 选型过程

### 方向选择

讨论过三个方向：

| 方向 | 考虑 | 结论 |
|---|---|---|
| AI 知识库助手（RAG） | 真实场景，技术覆盖广 | ✅ 作为基础能力 |
| AI Agent 助手 | 当前热门架构方向 | ✅ 作为核心架构 |
| LLM API 统一网关 | 偏 infra | ❌ 暂不选择 |

最终选择 **RAG + Agent 合体**。理由：Agent 做推理规划，RAG 提供知识支撑，真实企业应用基本都是合体架构。

### 垂直领域 vs 通用

最初犹豫是否做垂直领域。最终选择 **技术文档助手** 作为领域：
- 开发者理解开发者需求，不用额外学行业知识
- 数据好获取（GitHub 开源项目文档）

### 技术路线

在 Claude API 生态和 OpenAI 通用生态之间选择 **OpenAI 协议（千问）**：
- 通用协议，兼容更多模型和框架
- 用户可以切换到不同国产模型

### 学科知识点

- **Function Calling**：OpenAI API 的能力，模型输出结构化 JSON 参数
- **Registry**：管理 Function Schema 的上层抽象，Agent 循环中集中管理工具
- **ReAct**：思考→行动→观察→回答的循环模式
- **RAG**：检索增强生成，文档→切分→embed→检索→合成回答

### 学习路线建议

学习路径是：GitHub 开源项目 `learn_claude_code` → `hello_agents`（看到 memory 部分），然后开始自主构建项目。

### 关于框架（LangChain / LlamaIndex）

早期核心逻辑自实现（ReAct、RAG pipeline），深入理解底层原理。V4 之后加入框架适配层，对比自实现和框架方案的差异。
