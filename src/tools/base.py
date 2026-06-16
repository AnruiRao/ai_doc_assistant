from abc import ABC, abstractmethod
from pydantic import BaseModel

class Tool(ABC):
    """工具基类"""
    def __init__(self, name: str, description: str, input_model: type[BaseModel] | None = None):
        self.name = name
        self.description = description
        self.input_model = input_model

    @abstractmethod
    def run(self):
        pass

    def to_openai_tool(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema()
            }
        }