from core.agent import Agent
from core.llm import BaseLLM
from tools.registry import ToolRegistry
from core.config import Settings
from typing import Any
import json

DEFAULT_SYSTEM_PROMPT = "你是一个善于调用工具的ai助手。"

class ReactAgent(Agent):

    def __init__(
            self, 
            llm:BaseLLM | None = None, 
            system_prompt: str | None = None, 
            tool_registry: ToolRegistry | None = None, 
            config: Settings | None = None,
            max_steps: int = 10,
    ):
        system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        super().__init__(llm, system_prompt, tool_registry, config)
        self.max_steps = max_steps

    def run(self, input_text: str, history: list[dict[str, str]] | None = None, **kwargs) -> str:

        current_steps = 0
        history = history or []
        messages = self.build_messages(input_text, history)

        while current_steps < self.max_steps:
            current_steps += 1

            message =  self.llm.invoke_with_tools(
                messages=messages,
                tools=self.tools,
                tool_choice=kwargs.get("tool_choice", "auto")
            )

            if message.tool_calls:
                messages.append(message)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_arg = json.loads(tool_call.function.arguments)

                    tool = self.tool_registry.get_tool(tool_name)
                    if tool is None:
                        result = f"未找到工具：{tool_name}"
                    else:
                        try:
                            result = tool.run(**tool_arg)
                        except Exception as e:
                            result = f"执行工具{tool_name}时发生错误：{str(e)}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(result)
                    })

                continue
            
            if message.content is not None:
                return message.content
            
            raise RuntimeError("LLM 既没有返回文本内容，也没有触发工具调用。")
        
        raise RuntimeError(f"达到最大迭代次数 {self.max_steps}，任务未能完成。")