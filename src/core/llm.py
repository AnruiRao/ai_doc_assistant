from core.config import Settings, DEFAULT_PROVIDER
from openai import OpenAI
from core.exceptions import LLMException
from typing import Any

class BaseLLM:
    def __init__(
            self,
            api_key: str | None = None,
            base_url: str | None = None,
            config: Settings | None = None,
            model: str | None = None,
            provider: str  | None = None,
            temperature: float | None = None,
            timeout: int | None = None,
            **kwargs
    ):
        self.config = config or Settings.from_env()
        self.api_key = api_key or self.config.api_key
        self.base_url = base_url or self.config.base_url
        self.model = model or self.config.model
        self.temperature = temperature or self.config.temperature
        self.provider = provider or DEFAULT_PROVIDER
        self.timeout = timeout or self.config.timeout

        self.client = self._create_client()

    def invoke(self, messages: list[dict[str, str]], **kwargs):
        try:    
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMException(f"LLM调用失败: {str(e)}")
        
    def invoke_with_tools(
            self, 
            messages: list[dict[str, Any]], 
            tools: list[dict[str, Any]] | None = None,
            tool_choice: str | dict | None = None,
            **kwargs
    ):
            
        if tools:
            if tool_choice is None:
                tool_choice = "auto"
        else:
            tools = None
            tool_choice = None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
            return response.choices[0].message
        except Exception as e:
            raise LLMException(f"LLM调用失败: {str(e)}")

    def _create_client(self) -> OpenAI:
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )