"""验证 ReactAgent 基础工作流程。

运行前确保 .env 已配置好 LLM_API_KEY。
"""

import pytest

from tools.impl.calculator import CalculatorTool
from tools.registry import ToolRegistry
from agents.react_agent import ReactAgent


@pytest.mark.skip(reason="需要 LLM API key，CI 不运行")
def test_calculator_tool_turn():
    """注册计算器工具，让 Agent 调用它。"""
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())

    agent = ReactAgent(tool_registry=registry)

    result = agent.run("1 + 2 等于多少？")
    print(f"\nAgent 回答: {result}\n")

    assert "3" in result, f"预期结果包含 3，实际: {result}"
    print("✅ 测试通过：Agent 正确调用了计算器工具")


@pytest.mark.skip(reason="需要 LLM API key，CI 不运行")
def test_agent_direct_answer():
    """不依赖工具时，Agent 应直接回答。"""
    agent = ReactAgent()

    result = agent.run("你好，请简单介绍一下自己。")
    print(f"\nAgent 回答: {result}\n")

    assert len(result) > 10
    print("✅ 测试通过：Agent 能直接回答")


if __name__ == "__main__":
    test_calculator_tool_turn()
    test_agent_direct_answer()
