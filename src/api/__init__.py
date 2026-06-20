from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.exceptions import AssistantBaseError
from core.config import Settings
from core.llm import BaseLLM
from core.logging import configure_logging
from tools.registry import ToolRegistry
from tools.impl.rag_tool import RagTool
from tools.impl.calculator import CalculatorTool
from api.routes import health, chat


def create_app():
    app = FastAPI(title="AI Doc Assistant")

    # CORS — 允许 Streamlit 跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 异常 → HTTP 状态码映射
    @app.exception_handler(AssistantBaseError)
    async def assistant_error_handler(_: Request, exc: AssistantBaseError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )

    # 共享实例（跨请求复用 LLM 和 ToolRegistry）
    config = Settings.from_env()
    configure_logging()

    llm = BaseLLM(config=config)
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    registry.register_tool(RagTool())

    app.state.config = config
    app.state.llm = llm
    app.state.tool_registry = registry

    # 挂载路由
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, tags=["chat"])

    return app
