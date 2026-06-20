# 007: FastAPI + 异步桥接架构

- **日期**: 2026-06-20
- **状态**: 已实施

## 背景

V1 是 Streamlit 直调 ReactAgent 的单进程架构。V2 需要将 Agent 后端独立为 REST 服务，实现前后端分离。

## 架构决策

### 分层方式

```
Streamlit (8501) → HTTP → FastAPI (8000) → asyncio.to_thread → sync Agent
```

不引入 AsyncBaseLLM / AsyncAgent。Agent 循环是 CPU + I/O 混合型任务，用 `asyncio.to_thread` 扔到线程池跑即可，对事件循环无阻塞风险。

### App 工厂模式

使用 `create_app()` 函数而非全局 `app` 变量：

- 避免模块级共享状态
- 测试时可以创建独立的 app 实例
- 导入时不会执行副作用（如连接数据库）

### 共享实例策略

`BaseLLM` 和 `ToolRegistry` 在 `create_app()` 中创建一次，挂载到 `app.state`。路由通过 `request.app.state` 获取。每个请求新建轻量的 `ReactAgent` 实例。

### 异常映射

利用 FastAPI 的 `exception_handler`，将内部异常的 `status_code` 属性自动映射为 HTTP 状态码：

- `LLMRateLimitError(status_code=429)` → HTTP 429
- `LLMConnectionError(status_code=503)` → HTTP 503
- `ConfigurationError(status_code=500)` → HTTP 500

## 关键修复

上线过程中发现一个隐蔽的参数传递 bug：

`BaseLLM.__init__` 签名 `def __init__(self, api_key=None, base_url=None, config=None, ...)`，

调用 `BaseLLM(config)` 时，Settings 对象被当成了 `api_key` 参数传入，导致 `self.api_key` 类型为 `Settings` 而非 `str`。修复：`BaseLLM(config=config)`。

## 环境变量加载

`.env` 文件的加载方式：

1. **开发**：`./run_api.sh` 启动脚本自动加载 `.env`
2. **测试**：手动 `export` 或通过 `PYTHONPATH=src` 跑测试
3. **生产**：通过 Docker/k8s 注入环境变量，不使用 `.env`

`load_dotenv()` 保留在 `config.py` 中作为兜底，但不会覆盖已设置的变量。

## 后续计划

- **服务层提取**：将路由中的业务逻辑抽取为 DocumentService / AgentService
- **VectorStore 单例**：`get_vector_store()` 工厂 + 线程安全
- **测试 + CI**：Mock 测试、pytest-asyncio、GitHub Actions
