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

### ✅ V2 工程化（核心路径 + 增强已完成）
- [x] 异常体系（树形结构，可重试 vs 不可重试）
- [x] 重试机制（tenacity 指数退避）
- [x] 结构化日志（structlog，开发彩显 + 生产 JSON）
- [x] 文本噪声清理 + 递归分割（Phase 2 完成）
- [x] FastAPI REST API（`POST /chat`, `GET /health`）
- [x] 文档管理 API（上传 / 列表 / 删除）
- [x] 异步 Agent 桥接（asyncio.to_thread）
- [x] API 跨域支持（Streamlit + FastAPI 双进程）
- [x] Streamlit 瘦客户端（纯 httpx，剔除 Agent/Chroma 依赖）
- [x] 一键启动（`./run.sh` 同时拉起 FastAPI + Streamlit）
- [x] 全链路验证通过（API ↔ RAG ↔ Agent）
- [x] 服务层（DocumentService + routes 变薄 + rag_tool 去重）
- [x] 自动化测试 + CI（41 测试 + GitHub Actions workflows）

### 🔴 V3 实测驱动 RAG 优化（计划中）
- [ ] QA 评测集 + 指标系统
- [ ] Embedding 模型对比
- [ ] Reranker 两阶段检索
- [ ] Query rewrite / HyDE 等查询优化

## 快速开始

```bash
cp .env.example .env           # 填入 API Key 等信息
uv sync                         # 安装依赖

./run.sh                        # 一键启动（FastAPI + Streamlit）
```

### 环境变量

| 变量 | 说明 | 示例 |
|---|---|---|
| `LLM_API_KEY` | API Key | `sk-xxx` |
| `LLM_BASE_URL` | API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | 模型名 | `qwen3.6-max-preview`（默认） |

## 项目结构

```
src/
├── core/              抽象层（Config、LLM、Agent、异常、重试、日志）
├── tools/             工具系统（Tool 基类 + Registry）
│   └── impl/          工具实现（calculator、rag_tool）
├── agents/            ReAct Agent 实现
├── ingestion/         文档处理（loader、chunker）
├── retrieval/         向量检索（Chroma 封装）
├── app/               Streamlit 界面（瘦客户端，纯 httpx）
├── api/               FastAPI REST 服务
│   ├── main.py        入口
│   ├── __init__.py    工厂函数
│   ├── schemas/       Pydantic 请求/响应模型
│   └── routes/        路由（health / chat / documents）
└── services/          业务服务层（DocumentService）
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
- **V2 ✅** 工程化级 — 异常体系、重试、日志、FastAPI、文档管理 API、Streamlit 瘦客户端、服务层、测试+CI
- **V3 🔴 计划中** — 实测驱动的 RAG 优化（chunk、embedding、rerank、query rewrite）
- **V4** 生产化级 — Docker + 多用户 + 流式输出

详见 `PLAN.md` 和 `TASKS.md`。
