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
src/core/   src/services/   src/api/   src/retrieval/   src/app/
  │              │             │            │             │
  ├ exceptions   ├ Document    ├ routes     ├ singleton   ├ thin client
  ├ retry        ├ Agent       ├ schemas    ├ thread-safe └ → httpx → API
  ├ logging      ├ Chat        ├ DI wiring
  ├ AsyncBaseLLM └── 都调 API ─┘
  └ AsyncReactAgent
```

---

## 第四阶段：V2 工程化级

### Phase 1：基础设施

#### 1.1 pyproject.toml

- **文件**: `pyproject.toml`
- **改动**:
  - 版本号升 `0.1.0` → `0.2.0`
  - 加运行时依赖：`fastapi>=0.115.0`、`uvicorn[standard]>=0.34.0`、`httpx>=0.28.0`、`tenacity>=9.0.0`、`structlog>=25.0.0`
  - 加开发依赖：`pytest-asyncio>=0.25.0`、`ruff>=0.9.0`

#### 1.2 异常体系

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

#### 1.3 重试机制

- **文件**: `src/core/retry.py` (新)
- **实现**: tenacity 装饰器 `@llm_retry`
- **策略**: 最多 3 次，指数退避 1s→2s→4s，最大 10s
- **条件**: 只重试 `LLMConnectionError` / `LLMRateLimitError` / `LLMTimeoutError`
- **关键**: 需把 OpenAI SDK 的异常（`openai.APIConnectionError` 等）映射到我们的异常子类

#### 1.4 日志系统

- **文件**: `src/core/logging.py` (新)
- **实现**: structlog，开发环境彩显、生产 JSON
- **函数**: `configure_logging(level, json_output)` → FastAPI startup 调用
- **替换**: `ToolRegistry` 中的 `print()` → `logger.info()`

### Phase 2：异步化

#### 2.1 AsyncBaseLLM

- **文件**: `src/core/llm.py`（添加类，保留同步 `BaseLLM`）
- **实现**: 包装 `openai.AsyncOpenAI`，`async invoke()` + `async invoke_with_tools()`
- **异常映射**: 捕获 `openai.*Error` → 抛 `LLM*Error`
- **装饰器**: 方法上加 `@llm_retry`

#### 2.2 AsyncAgent ABC

- **文件**: `src/core/agent.py`（添加类）
- **要点**: `abstractmethod async def run()`，`build_messages()` 保持同步

#### 2.3 AsyncReactAgent

- **文件**: `src/agents/react_agent.py`（添加类）
- **要点**: Tool 执行用 `asyncio.to_thread(tool.run, **args)`，超限抛 `AgentError`

#### 2.4 异步工具

- **文件**: `src/core/async_utils.py`（新）
- **要点**: 统一 `run_in_thread(func)` 包装 `asyncio.to_thread`

### Phase 3：服务层

#### 3.1 DocumentService

- **文件**: `src/services/document_service.py`（新）
- **方法**: `async ingest_document()`、`async search_documents()`、`async delete_collection()`
- **输出**: Pydantic DTO（`DocumentIngestResult`, `SearchResult`）

#### 3.2 AgentService

- **文件**: `src/services/agent_service.py`（新）
- **方法**: `async chat(message, history)` → 运行 agent 循环
- **错误处理**: `AgentError` 返回部分回答，`LLMError` 向上抛

#### 3.3 ChatService

- **文件**: `src/services/chat_service.py`（新）
- **方法**: `get_or_create_history()`, `append_message()`, `clear_session()`
- **存储**: 内存 dict（V2 单用户足够，V4 换 Redis）

### Phase 4：FastAPI 应用

#### 4.1 目录结构

```
src/api/
├── __init__.py          create_app() 工厂
├── main.py              启动入口（uvicorn）
├── dependencies.py      FastAPI Depends 懒加载单例
├── routes/
│   ├── health.py        GET /health
│   ├── chat.py          POST /chat, GET /chat/{id}/history
│   └── documents.py     POST /documents/upload, POST /documents/search, DELETE /
└── schemas/
    ├── chat.py          ChatRequest, ChatResponse
    └── document.py      DocumentUploadResponse, SearchRequest, SearchResponse
```

#### 4.2 关键设计

- **App 工厂**: `create_app()` 而非全局 `app`，方便测试
- **DI**: 模块级 `global` 懒加载，首次请求才创建实例
- **CORS**: 允许 Streamlit（8501）跨域
- **异常映射**: AssistantBaseError 的 `status_code` → HTTP
- **中间件**: 请求日志（method/path/status）

### Phase 5：VectorStore 单例 + Streamlit 瘦身

#### 5.1 VectorStore 单例

- **文件**: `src/retrieval/vector_store.py`
- **改动**: 加 `get_vector_store()` 工厂，相同 (collection, persist) 返回同一实例
- **embedding**: 全局变量懒加载（只下载一次模型）
- **线程安全**: `add_documents` / `delete_collection` 加 `threading.Lock`
- **兼容**: 构造函数不变，旧代码 `VectorStore(...)` 仍可用

#### 5.2 Streamlit 瘦客户端

- **文件**: `src/app/ui.py`
- **改动**: 加 `USE_API` 环境开关
  - `USE_API=true` → httpx 调 FastAPI（`POST /chat`、`POST /documents/upload`）
  - `USE_API=false` → 直接用进程内 agent（开发模式）
- **注意**: `asyncio.run()` 包装异步调用

### Phase 6：测试 + CI

#### 6.1 测试新增

```
tests/
├── conftest.py              Mock AsyncOpenAI、TestClient、fixtures
├── unit/test_exceptions.py  异常体系
├── unit/test_retry.py       重试行为
├── unit/test_logging.py     日志配置
├── core/test_llm.py         AsyncBaseLLM + mock LLM
├── core/test_agent.py       AsyncReactAgent + mock
├── services/                服务层测试
├── api/                     FastAPI TestClient 路由测试
```

#### 6.2 CI

- **文件**: `.github/workflows/ci.yml`（新）
- **步骤**: uv → Python 3.12 → 依赖 → ruff lint + format → pytest
- **集成测试**: 仅在有 `LLM_API_KEY` secret 时运行

### Phase 7：基础 RAG 改进（不依赖评测）

肉眼可判断质量，不需要 QA 测试集。V2 间隙穿插，不阻塞主线。

#### 7.1 文本噪声清理

- **文件**: `src/ingestion/cleaner.py`（新）
- **实现**: 一个函数 `clean_text(raw: str) -> str`
- **规则**: 连续空行压缩（2+ → 1）、首尾空白修剪、特殊字符过滤（保留中文/英文/数字/常见标点）
- **注意**: 不做 Processor 框架抽象，一个函数解决问题

#### 7.2 递归分割

- **文件**: `src/ingestion/chunker.py`（改进）
- **改动**: 加 `recursive_split(text, chunk_size=500)` 函数
- **规则**: 优先按 `\n\n` 分段落 → 段落太长按 `\n` 分句 → 最后按字符截断
- **兼容**: 保留原有 `chunk_text()` 不动，新增函数可选使用

#### 7.3 集成到 rag_tool

- **文件**: `src/tools/impl/rag_tool.py`（改进）
- **改动**: save 模式先 `clean_text()` 再 chunk，默认用 `recursive_split`

### Phase 8：收尾验证 + 文档更新

#### 8.1 E2E 全链路验证

- **操作**: 启动 FastAPI + Streamlit，上传文档 → 对话 → 确认 Agent 正常回答
- **验收**: V1 功能在 V2 架构下完整可用

#### 8.2 文档更新

- `README.md`: 更新启动方式（FastAPI + Streamlit 双进程模式）
- `docs/decisions/`: 记录 Phase 1-8 的关键架构变更

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

## 第五阶段：V3 评估驱动 + RAG 优化级

### Phase 1：评测系统建立

先有评测，再做优化。所有 RAG 优化必须可测量、可对比。

#### 1.1 QA 测试集

- **文件**: `tests/eval/qa_dataset.json`（新）
- **内容**: 50-100 条 `{query, expected_answer, source_doc}` 三元组
- **来源**: 从实际使用的文档中人工标注

#### 1.2 评测指标

- **文件**: `src/evaluation/metrics.py`（新）
- **指标**:
  - `retrieval_recall@k` — 检索召回率
  - `answer_faithfulness` — 答案忠实度（是否幻觉）
  - `answer_completeness` — 答案完整性
- **输出**: 评测报告（Markdown 表格，对比每次改动前后）

#### 1.3 自动化评测 pipeline

- **文件**: `scripts/eval.py`（新）
- **流程**: 跑测试集 → 收集指标 → 输出对比报告

### Phase 2：RAG 优化

每一项优化都在评测集上对比 before/after。

#### 2.1 NoiseProcessor — 噪声清理

- **文件**: `src/ingestion/processors/text_processor.py`（新）
- **功能**: 页脚检测去除、连续空行压缩、特殊字符清理、多余空格整理
- **验收**: 脏文本输入 → 干净文本输出

#### 2.2 SmartChunker — 递归分割

- **文件**: `src/ingestion/chunker.py`（改进）
- **改动**: 加 `recursive_split(text, size=500)` 方法
- **规则**: 优先按 `\n\n` 分段落 → 段落太长按 `\n` 分 → 最后才按字符截断
- **验收**: chunk 边界落在自然断点，而非截断句子中间

#### 2.3 Embedding 模型对比

- **文件**: `src/retrieval/embedding.py`（新）
- **对比**: 当前 SentenceTransformer auto-embed vs 千问 text-embedding-v3（API）
- **验收**: 评测集上召回率对比

#### 2.4 Rerank 两阶段检索

- **文件**: `src/retrieval/reranker.py`（新）
- **架构**: 阶段 1 向量检索 top-50 → 阶段 2 Rerank 重排 → 返回 top-4
- **验收**: 相比纯向量检索，top-4 相关度明显提升

#### 2.5 增强元数据

- **文件**: `src/tools/impl/rag_tool.py`（改进）
- **改动**: metadata 加 `page_number`、`section_title`、`chunk_type`
- **验收**: 搜索结果可显示更详细的来源信息
