from __future__ import annotations
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "deepseek-v3"
DEFAULT_PROVIDER = "qwen"


class Settings(BaseModel):
    """配置类"""

    api_key: str = ""
    base_url: str = ""
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    timeout: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量获取配置"""
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", ""),
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
        )
