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

- **文件**: `src/ui/ui.py`
- **知识点**: Streamlit
- **补充**: 侧边栏文件上传（tempfile → rag_tool save），聊天对话（session_state 管理历史 + agent.run 传入 history）
- **验收**: 能上传文档、对话、Agent 回答正常
- **依赖**: 8, 5

---

### 任务 10：启动验证 ✅

- **操作**: 启动 Streamlit 测试全链路
- **验收**: 上传文档 → 检索 → Agent 回答，全通

```bash
uv run streamlit run src/ui/ui.py
```

- **依赖**: 9

---

**V1 Demo 阶段全部完成** 🎉

---

## 当前目录结构

```
src/
├── core/
│   ├── config.py          # 配置（Pydantic BaseModel）
│   ├── llm.py             # LLM 封装（invoke + invoke_with_tools）
│   ├── agent.py           # Agent 抽象基类
│   └── exceptions.py      # 异常体系
├── infra/
│   ├── retry.py           # tenacity 重试装饰器
│   └── logging.py         # structlog 结构化日志
├── tools/
│   ├── base.py            # Tool 抽象基类
│   ├── registry.py        # ToolRegistry 注册器
│   └── impl/
│       ├── calculator.py  # 计算器工具
│       └── rag_tool.py    # RAG 知识库工具（save/search/delete/list）
├── agents/
│   └── react_agent.py     # ReAct Agent 实现（市场监管领域 prompt）
├── ingestion/
│   ├── loader.py          # 文档加载器（.txt / .pdf）
│   ├── cleaner.py         # 文本噪声清理
│   ├── chunker.py         # 递归分割 + 短段合并
│   ├── gov_parser.py      # 政务文档章节识别与标记
│   └── web_loader.py      # 政务网页 HTML 提取
├── retrieval/
│   ├── vector_store.py    # Chroma 向量库封装
│   └── reranker.py        # Cross-encoder 精排
├── services/
│   └── document_service.py # 文档管理服务（上传/列表/删除/URL导入）
├── api/
│   ├── main.py            # uvicorn 入口
│   ├── __init__.py         # create_app() 工厂
│   ├── schemas/
│   │   ├── chat.py         # ChatRequest / ChatResponse
│   │   └── documents.py    # UploadResponse / IngestUrlRequest 等
│   └── routes/
│       ├── health.py       # GET /health
│       ├── chat.py         # POST /chat
│       └── documents.py    # 文档管理 + POST /ingest-url
└── ui/
    └── ui.py              # Streamlit 界面（瘦客户端 + URL 导入）
```

## 总依赖图

```
第一阶段（已完成）           第二阶段（已完成）        第三阶段（V1 已完成 🎉）
config → tools → react_agent ─┐
                               ├──→ rag_tool (✅) → ui (✅) → 验证 (✅)
                              loader → chunker → vector_store
                                        └→ 测试

第四阶段（V2 工程化级 ✅）

核心路径:
  Phase 1 (✅) → Phase 2 (RAG: cleaner + recursive chunk) → Phase 3 (FastAPI + async bridge)
                                                             ↓
                                                    Phase 4 (E2E verify + docs)

增强路径:
  ✅ 文档管理 API + Streamlit 瘦客户端
  🟡 服务层 (Document/Agent/Chat Service)
  🟡 测试 + CI (Mock + pytest-asyncio + GitHub Actions)
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

### Phase 3：FastAPI + 异步桥接 ✅ 已完成

#### 3.1 async_utils.py ✅

- **文件**: `src/core/async_utils.py`（新）
- **实现**: `run_in_thread(func, *args, **kwargs)` 包装 `asyncio.to_thread`
- **用途**: FastAPI 异步路由中调 sync Agent

#### 3.2 schemas/chat.py ✅

- **文件**: `src/api/schemas/chat.py`（新）
- **内容**: `ChatRequest(input_text, history)` + `ChatResponse(reply)`

#### 3.3 routes/health.py ✅

- **文件**: `src/api/routes/health.py`（新）
- **路由**: `GET /health` → `{"status": "ok"}`

#### 3.4 routes/chat.py ✅

- **文件**: `src/api/routes/chat.py`（新）
- **路由**: `POST /chat` → 创建 Agent → `asyncio.to_thread` → 返回回复
- **设计**: 通过 `request.app.state` 获取共享 LLM/ToolRegistry

#### 3.5 api/__init__.py ✅

- **文件**: `src/api/__init__.py`（新）
- **实现**: `create_app()` 工厂函数
- **内容**: CORS 中间件（localhost:8501）、异常→HTTP 映射、注册路由、共享实例初始化

#### 3.6 api/main.py ✅

- **文件**: `src/api/main.py`（新）
- **内容**: `app = create_app()` 暴露给 uvicorn

#### 3.7 run_api.sh ✅

- **文件**: `run_api.sh`（新）
- **内容**: 从项目根目录加载 `.env` 后启动 uvicorn

#### 3.8 修复问题 ✅

- `src/agents/react_agent.py`: `history` 参数加默认值 `None`
- `src/core/__init__.py`: `LLMException` → `LLMError`
- `src/core/logging.py`: 移除不兼容的 structlog processor（`filter_by_level`、`add_logger_name`）
- `src/api/__init__.py`: `BaseLLM(config)` → `BaseLLM(config=config)`（位置参数顺序 bug）

#### 启动方式

```bash
cd /Users/anrui/projects/ai_doc_assistant
./run_api.sh                        # 启动 FastAPI
curl localhost:8000/health           # 验证健康检查
curl -X POST localhost:8000/chat \  # 验证聊天
  -H "Content-Type: application/json" \
  -d '{"input_text":"你好","history":[]}'
```

### Phase 4：E2E 验证 + 文档更新 ✅ 已完成

#### 4.1 全链路验证 ✅

- **操作**: 启动 FastAPI + Streamlit，上传文档 → 对话 → 确认 Agent 正常回答
- **验收**: V1 功能在 V2 架构下完整可用，RAG 改进肉眼可感知
- **验证结果**:
  - `GET /health` → `{"status":"ok"}` ✅
  - `POST /chat` → Agent 正常回答 ✅
  - RAG save + search 全链路 via API ✅
  - Streamlit UI 正常启动 ✅

#### 4.2 文档更新 ✅

- `README.md`: V2 标记为已完成，添加增强路径状态
- `PLAN.md` / `TASKS.md`: 状态同步更新
- `docs/decisions/README.md`: 索引补充 007

---

### 增强路径（核心路径已完成 ✅）

**已完成的增强：**

#### 增强 2：文档管理 API + Streamlit 瘦客户端 ✅

- **文件**: `src/api/routes/documents.py`、`src/ui/ui.py`、`run.sh`
- **内容**:
  - FastAPI 文档管理接口：`POST /upload`、`GET /documents`、`DELETE /documents/{id}`
  - JSON 注册表 `data/documents.json` 追踪文档
  - Streamlit 去掉所有直接依赖（Agent/Chroma/ToolRegistry），纯 httpx 调后端
  - `./run.sh` 一键启动 FastAPI + Streamlit
- **收益**: Streamlit 秒级启动，分离部署，`run.sh` 一个命令跑全部

#### 增强 3：rag_tool 增强 + 去重 ✅

- **文件**: `src/tools/impl/rag_tool.py`、`src/api/routes/documents.py`
- **内容**:
  - rag_tool 新增 `list` 模式：Agent 可在对话中列举所有已上传文档
  - rag_tool `delete` 模式新增 `source` 参数：按路径删除指定文档，不传则清全库
  - 上传同名文件自动替换：先删旧的（Chroma + 磁盘 + 注册表）再存新的
- **收益**: Agent 可管理文档，避免重复文档污染知识库

#### 增强 4：服务层 ✅

- **文件**: `src/services/__init__.py`、`src/services/document_service.py`
- **内容**:
  - DocumentService 封装上传/列表/删除业务逻辑，统一注册表 + Chroma + 磁盘操作
  - `routes/documents.py` 路由变薄（~150→48 行），三条全 `def`，FastAPI 自动线程池
  - `rag_tool.py` 复用 DocumentService，删除重复的 `_load_registry` / `_save_registry`
- **收益**: 路由仅处理 HTTP 细节，业务逻辑集中在 Service 层；消除两处重复代码
- **注意**: AgentService 跳过（chat.py 已够薄），ChatService 跳过（尚无持久化需求）

**待回补：**

#### 测试 + CI ✅

- **文件**: `tests/test_documents.py`、`.github/workflows/ci.yml`
- **内容**: pytest 配置（asyncio_mode + testpaths）、DocumentService 测试（4 个）、API TestClient 路由测试（6 个）、GitHub Actions CI（uv sync → pytest → ruff check）
- **收益**: 每次 push 自动跑全部 94 个测试（V2: 41 + Phase A: 11 + Reranker/QR 等: 42），质量防线
- **注意**: `test_react_agent.py`（依赖真实 API key）加了 skip marker，CI 跳过；Agent 层暂无 mock 测试，后续有需求再补

---

### 启动方式

```bash
# 一键启动（默认）
./run.sh

# 或分进程启动
./run_api.sh                                    # FastAPI 单独
uv run streamlit run src/ui/ui.py              # Streamlit 单独

# 跑测试
cd /Users/anrui/projects/ai_doc_assistant
PYTHONPATH=src uv run pytest tests/ -v
```

---

## 第五阶段：V3 实测驱动 + RAG 优化级 ✅ 已完成

### 方法：目测优化 → 上指标 → 对比迭代

```
收集 20 条测试 query（已做完）
    ↓
目测优化 3 轮（已做完：chunk_size、搜索上限、滑动窗口）
    ↓
集成 RAGAS 评估 pipeline，出 baseline 分数（已做完 F=0.38 R=0.82）
    ↓
针对优化：chunk 合并 + BGE embedding（已做完）
    ↓
A2: Reranker 精排（已做完 F=0.68→0.79，+16%）
    ↓
A1: QR 完整实现（实施中：联合检索 + RRF 融合）
```

### Phase 1：收集问题集 ✅ 已完成

- **文件**: `docs/test-queries.md`
- **数量**: 20 条，覆盖宽泛查询、代码检索、决策原因、全流程、系统能力等类型
- **质量标记**: ✅ / ⚠️ / ❌，每轮改动后重跑对比

### Phase 2：目测优化（3 轮）✅ 已完成

#### 第 1 轮：chunk_size 500→1000
- **改动**: chunk_size 500→1000, chunk_overlap 50→100
- **效果**: query #1（V3 主要做什么？）从 ❌→✅，不再胡编

#### 第 2 轮：搜索上限代码硬拦截
- **改动**: `react_agent.py` 加 max_search=3，超出后强制模型回答
- **效果**: 避免 Agent 无意义地反复搜索，节省 token 同时避免死循环

#### 第 3 轮：滑动窗口上下文
- **改动**: `rag_tool.py` search 分支，命中 chunk 带回前后各 2 个相邻 chunk
- **效果**: #11（Docker 方案）⚠️→✅，#16（文档 pipeline）⚠️→✅
- **关键**: 修复了"检索到 PLAN.md 计划短语，但模型不知道它属于未来计划"的问题

### Phase 3：RAGAS 评估 pipeline ✅ 已完成

- **脚本**: `scripts/evaluate_rag.py`
- **功能**: 自动收集 Agent 回答 + contexts → RAGAS 评分（faithfulness + answer_relevancy）
- **特点**: 
  - 已有原始数据则跳过 Agent 阶段（省钱）
  - 支持断点续评（从 `data/eval_scores.json` 恢复进度）
  - 两次运行之间会自动跳过已评分项
- **当前数据**: 20/20 条全部完成 ✅
- **baseline 分数**: Faithfulness=0.38, Answer Relevancy=0.82
- **备注**: RAGAS 每次评分需额外 2 次 LLM 调用（拆 claim + 验证），20 条 ≈ 40 次额外调用

### Phase 4：针对性优化 ✅ 已完成

- ✅ 低分根因分析：chunker 碎片化 + embedding 模型中文弱
- ✅ 方案制定：决策记录 009（chunker 合并策略）、010（embedding 选型）
- ✅ 决策 009 实现：`_merge_short_chunks()` 阈值合并 + 11 个测试用例
- ✅ 决策 010：切换 BAAI/bge-base-zh-v1.5 → 重索引 → 重评验证
  - Faithfulness: 0.38 → **0.6353**（↑67%）
  - Answer Relevancy: 0.82 → **0.8819**（↑7.5%）

### V3 最新评估结果（Reranker 精排，温度 0，GLM-4.5-Air）

| 指标 | Baseline | +Reranker |
|------|:--------:|:---------:|
| **Faithfulness** | **0.6788** | **0.7883** (+16.1%) |
| **Answer Relevancy** | **0.8619** | **0.8664** (+0.5%) |

见详情：`data/eval_scores.json`。

### 垂直领域 Phase A：市场监管办事导办 ✅ 已完成

**数据基础层**

| 任务 | 文件 | 内容 |
|------|------|------|
| gov_parser | `src/ingestion/gov_parser.py` | 政务文档编号章节（一、二、三）和命名章节（办理材料/申请条件）识别与标记 |
| gov_parser 测试 | `tests/test_gov_parser.py` | 7 个用例：空文本/无匹配/编号章节/命名章节/混合/列表保护/非误标记 |
| web_loader | `src/ingestion/web_loader.py` | 政务网页 HTML→结构化文本，httpx 抓取 + 内容容器识别 + SSRF 防护 |
| web_loader 测试 | `tests/test_web_loader.py` | 4 个用例：简单HTML/不同class/无内容容器/网络异常 |

**集成层**

| 任务 | 文件 | 内容 |
|------|------|------|
| 数据处理链集成 | `src/services/document_service.py` + `src/tools/impl/rag_tool.py` | upload() 和 save 中 cleaner→**gov_parser**→chunker 全链路 |
| 导出新函数 | `src/ingestion/__init__.py` | 导出 tag_gov_sections + fetch_web_content |

**API 层**

| 任务 | 文件 | 内容 |
|------|------|------|
| IngestUrlRequest schema | `src/api/schemas/documents.py` | pydantic.HttpUrl 格式校验 |
| POST /ingest-url | `src/api/routes/documents.py` | URL→web_loader→cleaner→gov_parser→chunker→Chroma 全链路 |
| SSRF 防护 | `src/api/routes/documents.py` | URL scheme 校验 + 私有 IP/内网域名拦截 |
| URL 路由到 DocumentService | `src/api/routes/documents.py` | 获得去重 + 注册表 + 可删除能力 |

**应用层**

| 任务 | 文件 | 内容 |
|------|------|------|
| Agent prompt 替换 | `src/agents/react_agent.py` | 通用 prompt → 市场监管办事导办专用版本 |
| Streamlit URL 导入 | `src/ui/ui.py` | 侧边栏新增"从政务公开网址导入"输入框 |

**启动方式**

```bash
cd /Users/anrui/projects/ai_doc_assistant
./run.sh                                            # 一键启动（FastAPI + Streamlit）
curl -X POST localhost:8000/ingest-url -H "Content-Type: application/json" \
  -d '{"url":"https://www.xxx.gov.cn/..."}'        # 导入政务办事指南
```

**测试**：新增 11 个测试用例（gov_parser 7 + web_loader 4），总计 **94** 个测试。

### 待完成

- [x] ~~A1 QR 完整实现：改进 prompt + 联合检索 + RRF 融合~~（已实现，单一检索策略无收益，默认关）
- [x] ~~**垂直领域 Phase A**：市场监管办事导办~~（已确认方向并完成 Phase A）
- [x] **Phase D**：客户端角色分割（决策 014 ✅ 已实施）
  - [x] Streamlit 角色切换按钮（Session State 模式切换）
  - [x] 市民/管理员视图条件渲染
  - [x] 管理面板功能归纳（文件上传/URL导入/知识库管理）
  - [ ] 扩展功能（概览统计/检索测试/全量重索引）按需添加
- [x] **P0 Docker 部署**（ROADMAP.md P0 ✅ 已完成）
  - [x] Dockerfile + docker-compose.yml
  - [x] run.sh 本地/Docker 统一入口（替换 docker-entrypoint.sh）
  - [x] hf-cache volume 模型持久化
  - [ ] ~~Release v1.0.0 tag~~（当前 v0.5.x 远未达到 1.0，移除。v1.0 目标：待 Phase B/C/E + V3.5 全部完成后）
- [ ] **Phase E**：文档提取架构重构（决策 015，待讨论）
- [ ] **Phase B**：引导式导办对话 + 用户画像收集（交互轴升级）
- [ ] **Phase C**：结构化事项数据（JSON/SQLite）+ 条件→材料自动映射（数据轴升级）
- [ ] **V3.5 全链路异步化**：`OpenAI` → `AsyncOpenAI`，Agent+LLM+API 全 async，砍掉 `asyncio.to_thread`
- [ ] **V3.5 流式输出**：LLM stream → Agent async generator → FastAPI StreamingResponse
