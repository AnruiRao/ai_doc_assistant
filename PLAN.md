# AI 文档助手 — 项目规划

## 项目定位

一个带 RAG 能力的 AI Agent 助手，作为大模型应用开发的学习项目，逐步靠近生产级产品。

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

### V2 — 工程化级（预计 2 周，每日 2-3h）

**Phase 1：基础设施**
- 更新依赖（fastapi、uvicorn、httpx、tenacity、structlog）
- 异常体系树形化（`AssistantBaseError` → LLMError/AgentError/RetrievalError...）
- tenacity 重试（指数退避，区分可重试 vs 不可重试）
- structlog 结构化日志

**Phase 2：异步化**
- `AsyncBaseLLM` 包装 `AsyncOpenAI`，异常映射，`@llm_retry`
- `AsyncAgent` ABC 基类 + `AsyncReactAgent`
- Tool 保持同步，`asyncio.to_thread()` 桥接

**Phase 3：服务层**
- `DocumentService`（上传→切分→入库编排）
- `AgentService`（Agent 生命周期管理）
- `ChatService`（会话历史管理）

**Phase 4：FastAPI 应用**
- REST API（`POST /chat`、`POST /documents/upload`、`GET /health`）
- App 工厂模式 + DI 懒加载单例
- CORS + 异常→HTTP 状态码映射 + 请求日志中间件

**Phase 5：VectorStore 单例 + Streamlit 瘦身**
- `get_vector_store()` 单例工厂，embedding 模型全局懒加载
- 线程安全写入（`threading.Lock`）
- Streamlit 加 `USE_API` 开关，通过 httpx 调 FastAPI

**Phase 6：测试 + CI**
- Mock 测试（异常/重试/LLM/Agent）+ API 路由测试（TestClient）
- Ruff lint + format + GitHub Actions

**Phase 7：基础 RAG 改进（V2 间隙穿插）**
- 文本噪声清理（空行压缩、特殊字符过滤）
- 递归分割（优先段落边界切分，不改变原有固定切分）
- 集成到 rag_tool save 流程
- 不引入新依赖，一个函数解决问题，不做框架抽象

**Phase 8：收尾验证 + 文档更新**
- E2E 全链路验证（FastAPI + Streamlit 双进程）
- README 更新、决策记录补充

> **V2 → V3 承上启下**：V2 搭建的 AsyncBaseLLM 支持快速切换 embedding 模型，VectorStore 单例方便替换检索后端，服务层为 Rerank 预留了接口。V2 搭好实验台，V3 跑实验。

详细实施计划见 `.claude/plans/scalable-honking-popcorn.md`。

### V3 — 评估驱动 + RAG 优化级（+3-4 周）

**评估系统（驱动决策）**
- 构建高质量 QA 测试集（50-100 条领域标注）
- 准确率、召回率、忠实度、答案完整性指标
- 自动化评测 pipeline
- 链路追踪（trace 每个请求的输入→检索→输出）
- 用户反馈系统

**RAG 优化（由评测数据驱动）**
- 噪声处理器（页脚去除、空行压缩、乱码清理）
- SmartChunker 递归分割（段落优先切分，而非固定字符）
- 对比不同 chunk_size、chunk_overlap 对召回率的影响
- 对比 auto-embed（SentenceTransformer）与 API-based embedding（千问 text-embedding-v3）
- Rerank 两阶段检索（向量检索 → 重排序）
- 增强元数据（页码、章节标题、chunk_type），提升可追溯性

> 核心规则：**先有评测，再做优化**。每一项改动都在评测集上对比 before/after，用数据说话。

### V4 — 生产化级（+3-4 周）

- Docker + docker-compose 部署
- 多用户 + Session 管理
- 缓存（Redis）
- API 鉴权 + 速率限制
- 流式输出 + 打字机效果
- 异步文档处理队列
- **`@tool` 装饰器**：在 `src/tools/` 下自实现 `@tool` 装饰器，展示语法糖与基类继承的对比
- **LangChain 适配器**：在 `src/vendor/` 下加入 LangChain 对比实现或适配层

### V5 — 深度进阶级（可选）

- 知识图谱 RAG / GraphRAG
- 多模态（代码截图、图表识别）
- 模型路由（简单问题用小模型）
- Prompt 注入防护
- 成本追踪

---

## 当前进度

**V1 Demo 阶段已全部完成** ✅ — Agent 核心 + RAG 检索 + Streamlit UI + 全链路验证。

**当前：V2 工程化级（进行中）** — 见上方详细计划，预计 2 周。

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
| **V2 工程化** | 文件名+序号 | 先按 metadata.source 删除旧 chunks，再重新插入 | 每个文件始终一份，ID 可读 | 需要 VectorStore 支持按条件删除 |
| **V3 评测驱动** | 内容哈希 | MD5(chunk) 做 ID，内容不变 ID 不变 | 确定性、可复现评测、自动去重 | 哈希碰撞理论风险极低 |
| **V4 生产化** | 文件名+序号+用户ID | 拼接 user123_doc.txt_0 | 多用户天然隔离 | ID 变长 |

**V1 当前实现要点**：
- `ids = [str(uuid4()) for _ in chunks]` — 永远不碰撞
- `metadatas` 存 `{"source": path, "chunk_index": i}` — 搜索结果可显示来源
- search 返回 `[来源: xxx]` 标签 — Agent 能告知用户信息出处
- delete 模式先 `vs.count()` 检查再删除 — 空集合不误报"已删除"
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
