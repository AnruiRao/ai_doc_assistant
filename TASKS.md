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

### 任务 9：ui.py

- **文件**: `src/app/ui.py`
- **知识点**: Streamlit
- **验收**: 能上传文档、对话、Agent 回答正常
- **依赖**: 8, 5

---

### 任务 10：启动验证

- **操作**: 启动 Streamlit 测试全链路
- **验收**: 上传文档 → 检索 → Agent 回答，全通

```bash
uv run streamlit run src/app/ui.py
```

- **依赖**: 9

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
└── app/                 # （待实现）
```

## 总依赖图

```
第一阶段（已完成）           第二阶段（已完成）        第三阶段（当前）
config → tools → react_agent ─┐
                               ├──→ rag_tool (✅) → ui → 验证
                              loader → chunker → vector_store
                                        └→ 测试
