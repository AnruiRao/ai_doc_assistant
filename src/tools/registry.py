from pydantic import BaseModel
from tools.base import Tool

class ToolRegistry:
    """工具注册类"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        if tool.name in self._tools:
                print(f"工具：{tool.name}已存在,将被覆盖")
        self._tools[tool.name] = tool
        print(f"工具：{tool.name}注册成功")

    def get_tool(self, name: str) -> Tool | None:
        """获取指定Tool对象"""
        if name in self._tools:
            return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_all_tools(self) -> list[Tool]:
        """获取所有Tool对象"""
        return list(self._tools.values())
    
    def unregister(self, name: str):
        """注销指定工具
        - name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            print(f"已注销工具：{name}")
        else:
            print(f"未找到工具：{name}")

    def clear(self):
        """清除所有工具"""
        self._tools.clear()

    def to_openai_tools(self):
        return [tool.to_openai_tool() for tool in self._tools.values()]
        