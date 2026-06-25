from core.agent import Agent
from core.llm import BaseLLM
from tools.registry import ToolRegistry
from core.config import Settings
import json

DEFAULT_SYSTEM_PROMPT = """你是一个善于调用工具的 AI 助手。请遵循 ReAct 模式工作：

1. 思考当前需要做什么，必要时调用工具获取信息
2. 根据工具返回的结果推理并回答用户的问题
3. 当工具返回的信息足够回答问题时，直接给出完整答案，不要重复调用同一个工具
4. 如果工具返回的结果无法回答问题，尝试换一种方式搜索后再回答
5. 搜索知识库最多 3 次，如果 3 次都找不到相关信息，就根据已有知识回答"""

class ReactAgent(Agent):

    def __init__(
            self, 
            llm:BaseLLM | None = None, 
            system_prompt: str | None = None, 
            tool_registry: ToolRegistry | None = None, 
            config: Settings | None = None,
            max_steps: int = 15,
    ):
        system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        super().__init__(llm, system_prompt, tool_registry, config)
        self.max_steps = max_steps

    def run(self, input_text: str, history: list[dict[str, str]] | None = None, **kwargs) -> str:

        current_steps = 0
        search_count = 0
        max_search = 3
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

                    # 代码级拦截：搜索知识库超过上限后不再执行，强制模型回答
                    if tool_name == "rag_tool" and tool_arg.get("use_for") == "search":
                        search_count += 1
                        if search_count > max_search:
                            result = "已达到最大搜索次数(3次)，请基于已有信息和你的知识回答，不要再调用搜索工具。"
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": result
                            })
                            continue

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