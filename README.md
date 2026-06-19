# AI 文档助手

基于自实现 RAG + ReAct Agent 的智能文档问答系统。

## 功能

### ✅ V1 Demo（已完成，当前可用）
- [x] 上传文档（.txt / .pdf）
- [x] 文档自动切分 + Chroma 向量化存储
- [x] 语义检索（cosine similarity，top-k 可配）
- [x] ReAct Agent 对话（思考→行动→观察循环）
- [x] 工具调用（计算器、RAG 知识库）
- [x] 聊天上下文记忆（多轮对话）
- [x] 文档清理（空行压缩、特殊字符过滤）— Phase 2.1
- [x] 递归分割（按段落→句子→字符优先级）— Phase 2.2
- [x] RAG 工具集成（save 前自动 clean + 递归切分）— Phase 2.3
- [x] Streamlit Web UI

### 🟢 V2 工程化（进行中，Phase 3 待开始）
- [x] 异常体系（树形结构，可重试 vs 不可重试）
- [x] 重试机制（tenacity 指数退避）
- [x] 结构化日志（structlog，开发彩显 + 生产 JSON）
- [x] 文本噪声清理 + 递归分割（Phase 2 完成）
- [ ] FastAPI REST API（`POST /chat`, `GET /health`）
- [ ] 异步 Agent 桥接（asyncio.to_thread）
- [ ] 自动化测试（目标 31+ 用例）
- [ ] API 跨域支持（Streamlit + FastAPI 双进程）

### 🔴 V3 实测驱动 RAG 优化（计划中）
- [ ] QA 评测集 + 指标系统
- [ ] Embedding 模型对比
- [ ] Reranker 两阶段检索
- [ ] Query rewrite / HyDE 等查询优化

## 快速开始

```bash
cp .env.example .env           # 填入 API Key 等信息
uv sync                         # 安装依赖

# 模式一：直接启动 Streamlit（V1 模式）
uv run streamlit run src/app/ui.py

# 模式二：启动 FastAPI 服务（V2 模式）
uv run uvicorn src.api.main:app --reload --port 8000
```

### 环境变量

| 变量 | 说明 | 示例 |
|---|---|---|
| `LLM_API_KEY` | API Key | `sk-xxx` |
| `LLM_BASE_URL` | API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | 模型名 | `deepseek-v3`（默认） |

## 项目结构

```
src/
├── core/              抽象层（Config、LLM、Agent、异常、重试、日志）
├── tools/             工具系统（Tool 基类 + Registry）
│   └── impl/          工具实现（calculator、rag_tool）
├── agents/            ReAct Agent 实现
├── ingestion/         文档处理（loader、chunker）
├── retrieval/         向量检索（Chroma 封装）
├── app/               Streamlit 界面
├── api/               FastAPI REST 服务（V2）
└── services/          业务服务层（V2 增强）
```

## 技术栈

| 层 | 选型 |
|---|---|
| Agent | 自实现 ReAct 循环（不依赖 LangChain） |
| RAG | 自实现 pipeline（loader → chunker → vector store） |
| 向量库 | Chroma（SentenceTransformer embedding） |
| LLM API | OpenAI 兼容协议（千问 / DeepSeek 等） |
| 后端 | FastAPI（V2 工程化） |
| 前端 | Streamlit |

## 发展阶段

- **V1 ✅** Demo 级 — Agent 核心 + RAG 检索 + Streamlit UI 全链路跑通
- **V2 🟢 进行中** — Phase 2（RAG 基础优化）已完成，Phase 3（FastAPI + 异步）待开始
- **V3 🔴 计划中** — 实测驱动的 RAG 优化（chunk、embedding、rerank、query rewrite）
- **V4** 生产化级 — Docker + 多用户 + 流式输出

详见 `PLAN.md` 和 `TASKS.md`。
