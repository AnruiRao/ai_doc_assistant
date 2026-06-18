# AI 文档助手

基于自实现 RAG + ReAct Agent 的智能文档问答系统。

## 功能

- 上传 `.txt` / `.pdf` 文档 → 自动切分 → 向量化存储
- 对话式提问 → Agent 自主检索相关内容 → LLM 合成回答
- 聊天上下文记忆（支持多轮对话）
- 内置计算器工具（Agent 自动决定是否调用）

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
- **V2 ✅ 进行中** 工程化级 — 异常体系、重试、日志、RAG 基础优化、FastAPI 服务化
- **V3** 实测驱动级 — 真实问题驱动 RAG 优化（chunk、embedding、rerank）
- **V4** 生产化级 — Docker + 多用户 + 流式输出

详见 `PLAN.md` 和 `TASKS.md`。
