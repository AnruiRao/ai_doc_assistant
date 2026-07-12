from __future__ import annotations
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "deepseek-v3"
DEFAULT_PROVIDER = "qwen"
SIMILARITY_THRESHOLD = 1.0


class Settings(BaseModel):
    """配置类"""

    api_key: str = ""
    base_url: str = ""
    model: str = DEFAULT_MODEL
    temperature: float = 0.3
    timeout: int = 60
    enable_query_rewrite: bool = False
    enable_reranker: bool = True
    similarity_threshold: float = SIMILARITY_THRESHOLD

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量获取配置"""
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", ""),
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
            enable_query_rewrite=os.getenv("ENABLE_QUERY_REWRITE", False),
            enable_reranker=os.getenv("ENABLE_RERANKER", True),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", SIMILARITY_THRESHOLD)),
        )
