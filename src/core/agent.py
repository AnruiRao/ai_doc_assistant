from abc import ABC, abstractmethod
from core.llm import BaseLLM
from tools.registry import ToolRegistry
from core.config import Settings
from typing import Any

class Agent(ABC):

    def __init__(
            self,
            llm: BaseLLM | None = None,
            system_prompt: str | None = None,
            tool_registry: ToolRegistry | None = None,
            config: Settings | None = None
    ):
        self.llm = llm or BaseLLM()
        self.system_prompt = system_prompt
        self.config = config or Settings.from_env()

        self.tool_registry = tool_registry
        self.tools = tool_registry.to_openai_tools() if tool_registry else None

    @abstractmethod
    def run(self):
        pass


    def build_messages(self, input_text: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_text}
        ]
        return messages