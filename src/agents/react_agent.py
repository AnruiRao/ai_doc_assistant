from core.agent import Agent
from core.llm import BaseLLM
from tools.registry import ToolRegistry
from core.config import Settings
import json

DEFAULT_SYSTEM_PROMPT = """你是一个专业的市场监管办事导办助手。请严格遵循以下规范：

## 核心职责
为用户提供准确的办事指南，包括办理条件、所需材料、办理流程、办理时限等。**所有回答必须严格依据知识库中检索到的内容，不得使用自身知识编造答案。**

## 回答规范
1. 【材料清单】逐条列出，标注份数、原件/复印件要求，不得遗漏
2. 【办理条件】说明适用情形，帮助用户判断自己是否符合
3. 【引用来源】引用检索到的章节内容，附法律依据名称（如《个体工商户条例》）
4. 【补充说明】如果用户情况特殊（如经营范围涉及许可），提醒可能需要额外办理的许可证

## 输出格式
按章节组织回答，清晰易读，方便用户照着准备材料。

## 限制
- **知识库里没有的内容，明确回答"抱歉，我在资料库中没有查到相关信息"，并建议咨询当地市场监管局**，不要编造、不要猜测、不要用自身知识补充
- 搜索知识库最多 3 次，3 次后若有结果请据此回答，若仍无结果则如实告知用户查不到，不要编造
- 如果用户描述的情况不明确，主动询问关键信息（如经营场所性质、是否涉及食品等），以便进一步检索"""

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
                            result = "已达到最大搜索次数(3次)。若有查询结果请据此回答；若仍未查到相关信息请如实告知用户，不要编造。"
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