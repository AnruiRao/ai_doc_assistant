# 开发任务清单

## 三个阶段

```
第一阶段：Agent 核心   → 第二阶段：RAG 检索   → 第三阶段：整合上线
```

---

## 第一阶段：Agent 核心 ✅ 已完成

### 任务 1：config.py ✅

- **文件**: `src/core/config.py`
- **知识点**: python-dotenv，Pydantic BaseModel
- **补充**: 使用了 `from_env()` 工厂方法实例化

### 任务 2：工具系统 ✅

- **文件**: `src/tools/base.py` + `src/tools/registry.py`
- **知识点**: ABC 抽象基类，OpenAI tool schema，Pydantic input_model
- **补充**: `Tool` 是抽象基类（非简单类），`ToolRegistry` 管理注册/查找/注销/清空

### 任务 3：react_agent.py ✅

- **文件**: `src/agents/react_agent.py`
- **知识点**: Agent 抽象基类继承，ReAct 循环，tool_calls 处理
- **补充**: 继承自 `Agent`（ABC 基类），`BaseLLM` 有 `invoke_with_tools()` 返回消息对象

### 已完成的支撑文件

- `src/core/agent.py` — Agent 抽象基类
- `src/core/llm.py` — BaseLLM 封装（invoke + invoke_with_tools）
- `src/core/exceptions.py` — 异常体系

---

## 第二阶段：RAG 检索 ✅ 已完成

### 任务 4：loader.py ✅

- **文件**: `src/ingestion/loader.py`
- **知识点**: pypdf，文件 IO，Pathlib
- **补充**: 三个函数 `load_text` / `load_pdf` / `load_document`，自动识别 `.txt` 和 `.pdf`
- **验收**: 能加载 `.txt` 和 `.pdf` 返回字符串
- **测试**: `TestLoader` 5 个用例（正常加载 + 格式校验 + 文件不存在）

---

### 任务 5：chunker.py ✅

- **文件**: `src/ingestion/chunker.py`
- **知识点**: 字符串操作，游标法切片
- **补充**: `while start < len(text)` + 游标回溯实现重叠，`chunk_overlap >= chunk_size` 抛异常
- **验收**: 长文本切成多块，相邻块有重叠
- **测试**: `TestChunker` 6 个用例（基础切分 + 重叠验证 + 小文本 + 精确尺寸 + 空文本 + 重叠内容验证）

---

### 任务 6：pytest 测试 ✅

- **文件**: `tests/test_retrieval.py`
- **知识点**: pytest，tmp_path fixture，Chroma 集合生命周期管理，pypdf PdfWriter 生成测试夹具
- **验收**: 17 个测试用例全部通过
- **补充**: VectorStore 测试用 `tmp_path` 隔离持久化，测试后 `delete_collection()` 清理

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_retrieval.py -v
```

---

### 任务 7：vector_store.py ✅

- **文件**: `src/retrieval/vector_store.py`
- **知识点**: Chroma PersistentClient，auto-embedding SentenceTransformer
- **补充**: 
  - 使用 `paraphrase-multilingual-MiniLM-L12-v2`（中文友好）
  - 当前 auto-embed 方式，未来可转手动（详见 PLAN.md）
  - 4 个方法：`add_documents` / `similarity_search` / `count` / `delete_collection`
- **验收**: 能写入文档片段，能检索出相关内容
- **测试**: `TestVectorStore` 4 个用例（增搜 + 元数据 + 空库 + 集合重建）

---

## 第三阶段：整合

### 任务 8：rag_tool.py ✅

- **文件**: `src/tools/impl/rag_tool.py`
- **知识点**: 继承 Tool 抽象基类，多模式 InputModel 设计，LLM 友好的 Field description
- **验收**: save 模式存文档 → chunk → 向量化，search 模式检索 → 返回格式化结果
- **补充**: 修复了 3 个原始问题：
  - `f"字符串"` 不可 raise → 改为 return 错误字符串（Tool 场景下让 Agent 自己处理而非抛异常）
  - `Chunker(None, None)` 崩溃 → 参数全设默认值，`run()` 内校验各模式必填字段
  - `use_for` 不分模式 → schema 仅 `use_for` 为必填，`[save 模式]` / `[search 模式]` 标签在 description 区分
- **依赖**: 3, 7

---

### 任务 9：ui.py ✅

- **文件**: `src/app/ui.py`
- **知识点**: Streamlit
- **补充**: 侧边栏文件上传（tempfile → rag_tool save），聊天对话（session_state 管理历史 + agent.run 传入 history）
- **验收**: 能上传文档、对话、Agent 回答正常
- **依赖**: 8, 5

---

### 任务 10：启动验证 ✅

- **操作**: 启动 Streamlit 测试全链路
- **验收**: 上传文档 → 检索 → Agent 回答，全通

```bash
uv run streamlit run src/app/ui.py
```

- **依赖**: 9

---

**V1 Demo 阶段全部完成** 🎉

---

## 当前目录结构

```
src/
├── core/
│   ├── config.py        # 配置（Pydantic BaseModel）
│   ├── llm.py           # LLM 封装（invoke + invoke_with_tools）
│   ├── agent.py         # Agent 抽象基类
│   └── exceptions.py    # 异常
├── tools/
│   ├── base.py          # Tool 抽象基类
│   ├── registry.py      # ToolRegistry 注册器
│   └── impl/
│       ├── calculator.py  # 计算器工具
│       └── rag_tool.py    # RAG 知识库工具
├── agents/
│   └── react_agent.py   # ReAct Agent 实现
├── ingestion/
│   ├── loader.py        # 文档加载器（.txt / .pdf）
│   └── chunker.py       # 文本切分器（chunk_size + chunk_overlap）
├── retrieval/
│   └── vector_store.py  # Chroma 向量库封装
└── app/
    └── ui.py          # Streamlit 界面
```

## 总依赖图

```
第一阶段（已完成）           第二阶段（已完成）        第三阶段（V1 已完成 🎉）
config → tools → react_agent ─┐
                               ├──→ rag_tool (✅) → ui (✅) → 验证 (✅)
                              loader → chunker → vector_store
                                        └→ 测试

第四阶段（V2 工程化级 ⏳）

核心路径:
  Phase 1 (✅) → Phase 2 (RAG: cleaner + recursive chunk) → Phase 3 (FastAPI + async bridge)
                                                             ↓
                                                    Phase 4 (E2E verify + docs)

增强路径（核心完成后回补）:
  ├ 服务层 (Document/Agent/Chat Service)
  ├ VectorStore 单例 + Streamlit 瘦客户端
  └ 测试 + CI (Mock + pytest-asyncio + GitHub Actions)
```

---

## 第四阶段：V2 工程化级

**核心路径**（按顺序做完即为 V2 完成）→ **增强路径**（时间充裕再回补）

### 核心路径

### Phase 1：基础设施 ✅ 已完成

#### 1.1 pyproject.toml ✅

- **文件**: `pyproject.toml`
- **改动**:
  - 版本号升 `0.1.0` → `0.2.0`
  - 加运行时依赖：`fastapi>=0.115.0`、`uvicorn[standard]>=0.34.0`、`httpx>=0.28.0`、`tenacity>=9.0.0`、`structlog>=25.0.0`
  - 加开发依赖：`pytest-asyncio>=0.25.0`、`ruff>=0.9.0`

#### 1.2 异常体系 ✅

- **文件**: `src/core/exceptions.py`
- **改动**: 单类 `LLMException` → 树形体系
  ```
  AssistantBaseError
  ├── ConfigurationError   (500，环境变量缺失)
  ├── LLMError
  │   ├── LLMConnectionError   (可重试)
  │   ├── LLMRateLimitError    (可重试)
  │   ├── LLMTimeoutError      (可重试)
  │   └── LLMApiError          (不可重试)
  ├── AgentError           (max_steps 超限)
  ├── RetrievalError       (ChromaDB 异常)
  └── DocumentError        (文件格式/解析)
  ```
- **知识点**: 各异常带 `status_code` 属性，FastAPI 按此映射 HTTP 状态码

#### 1.3 重试机制 ✅

- **文件**: `src/core/retry.py` (新)
- **实现**: tenacity 装饰器 `@llm_retry`
- **策略**: 最多 3 次，指数退避 1s→2s→4s，最大 10s
- **条件**: 只重试 `LLMConnectionError` / `LLMRateLimitError` / `LLMTimeoutError`

#### 1.4 日志系统 ✅

- **文件**: `src/core/logging.py` (新)
- **实现**: structlog，开发环境彩显、生产 JSON
- **函数**: `configure_logging(json_output)` → FastAPI startup 调用
- **替换**: `ToolRegistry` 中的 `print()` → `logger.info()`

### Phase 2：基础 RAG 改进（能力优先）

先把 RAG 质量提上去，让用户看到 Agent 回答变好，再做工程化。

#### 2.1 文本噪声清理 ✅

- **文件**: `src/ingestion/cleaner.py`（新）
- **实现**: 一个函数 `clean_text(raw: str) -> str`
- **规则**: 连续空行压缩（2+ → 1）、首尾空白修剪、特殊字符过滤（白名单：中文/英文/数字/常见标点）、全角空格→半角
- **注意**: 不做 Processor 框架抽象
- **测试**: `TestCleaner` 8 个用例（空文本、首尾空白、连续空行、特殊字符、中文保留、全角空格、完整流程）

#### 2.2 递归分割 ✅

- **文件**: `src/ingestion/chunker.py`（改进）
- **改动**: 加 `recursive_split(text, chunk_size=500)` 函数
- **规则**: 优先按 `\n\n` 分段落 → 段落太长按 `\n` 分句 → 最后按字符截断
- **兼容**: 保留原有 `chunk_text()` 不动
- **测试**: `TestRecursiveSplit` 6 个用例（空文本、短文本、多段落、长段落按行切、超长行硬切、混合场景）

#### 2.3 集成到 rag_tool ✅

- **文件**: `src/tools/impl/rag_tool.py`（改进）
- **改动**: save 模式先 `clean_text()` 再 chunk，默认用 `recursive_split`

### Phase 3：FastAPI + 异步桥接

#### 3.1 异步工具

- **文件**: `src/core/async_utils.py`（新）
- **实现**: 一个函数 `run_in_thread(func, *args)` 包装 `asyncio.to_thread`
- **用途**: FastAPI 异步路由中调 sync Agent

#### 3.2 目录结构

```
src/api/
├── __init__.py          create_app() 工厂
├── main.py              启动入口（uvicorn）
├── routes/
│   ├── health.py        GET /health
│   └── chat.py          POST /chat
└── schemas/
    └── chat.py          ChatRequest, ChatResponse
```

#### 3.3 关键设计

- **App 工厂**: `create_app()` 而非全局 `app`
- **异常映射**: AssistantBaseError 的 `status_code` → HTTP
- **CORS**: 允许 Streamlit（8501）跨域
- **简化**: 不涉及服务层，Agent 路由 `await asyncio.to_thread(agent.run, ...)`
- **不做**: AsyncBaseLLM、AsyncAgent ABC、AsyncReactAgent（V2 不需要两套 Agent）

### Phase 4：E2E 验证 + 文档更新

#### 4.1 全链路验证

- **操作**: 启动 FastAPI + Streamlit，上传文档 → 对话 → 确认 Agent 正常回答
- **验收**: V1 功能在 V2 架构下完整可用，RAG 改进肉眼可感知

#### 4.2 文档更新

- `README.md`: 更新启动方式
- `docs/decisions/`: 记录 V2 关键架构变更

---

### 增强路径（核心路径完成后，时间充裕再回补）

#### 增强 1：服务层

- **文件**: `src/services/document_service.py`、`src/services/agent_service.py`、`src/services/chat_service.py`
- **内容**: 将 FastAPI 路由中的逻辑抽取为 Service 层，DocumentService 编排上传→入库，AgentService 管理 Agent 生命周期，ChatService 管理会话历史
- **收益**: 路由更薄，业务逻辑可复用、可单独测

#### 增强 2：VectorStore 单例 + Streamlit 瘦客户端

- **文件**: `src/retrieval/vector_store.py`、`src/app/ui.py`
- **内容**: `get_vector_store()` 单例工厂、线程安全、`USE_API` 开关
- **收益**: Streamlit 通过 httpx 调 FastAPI，分离部署

#### 增强 3：测试 + CI

- **文件**: `tests/` 目录、`.github/workflows/ci.yml`
- **内容**: Mock 测试、pytest-asyncio、TestClient 路由测试、GitHub Actions
- **收益**: 自动化质量保障

### 启动方式

```bash
# 启动 FastAPI
uv run uvicorn api.main:app --reload --port 8000

# 启动 Streamlit（调用 API 模式）
USE_API=true uv run streamlit run src/app/ui.py

# 跑测试
uv run pytest tests/unit tests/core tests/services tests/api -v
```

---

## 第五阶段：V3 实测驱动 + RAG 优化级

### 方法：问题驱动循环，不是指标驱动

```
日常使用 → 收集问题（15-20 个回答不好的 query）
    ↓
定位最突出的 1 个瓶颈
    ↓
做一次针对性改动（只改一个变量）
    ↓
用同批问题重跑，肉眼对比
    ↓
重复直至收敛
```

不预先搭建评测系统（标注成本被严重低估），不设预设优化顺序（瓶颈取决于实际使用）。

### Phase 1：收集问题集

- **操作**: 日常使用中记录 Agent 回答不好的问题
- **数量**: 15-20 条
- **格式**: 自由文本，记下 query + 不满意的原因（"回答了但没有引用来源"、"检索出来的内容不对"等）
- **不需要**: 标准答案、结构化标注、人工评分

### Phase 2：诊断 + 针对性优化

重复以下循环：

1. 用当前问题集跑一遍 Agent，记录表现
2. 观察最明显的共性问题（召回差？chunk 切断语义？噪声干扰？）
3. 针对该问题做一次改动
4. 用同批问题再跑，对比改善程度
5. 如果有效，保留改动；如果无效，回退

**可能触及的改动方向**（不做预设，诊断到哪改到哪）：
- 递归分割 vs 固定分割对比
- 噪声清理前后对比
- embedding 模型替换实验
- Rerank 两阶段检索

### Phase 3：收敛判断

- **暂停条件**: 连续 2-3 轮改动后肉眼已无法感知改善
- **后续选择**:
  - 满足于当前质量，进入 V4
  - 或如果仍有模糊的提升空间，此时再考虑建正式评测集做定量分析
