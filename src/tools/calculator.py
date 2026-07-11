from pydantic import BaseModel, Field
from tools.base import Tool


class CalculatorInput(BaseModel):
    a: float = Field(description="第一个数字")
    b: float = Field(description="第二个数字")
    op: str = Field(default="+", description="运算符，支持 +、-、*、/")


class CalculatorTool(Tool):
    """基础计算器工具，支持加减乘除。"""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，支持加(+)减(-)乘(*)除(/)运算",
            input_model=CalculatorInput,
        )

    def run(self, a: float, b: float, op: str = "+") -> str:
        if op == "+":
            result = a + b
        elif op == "-":
            result = a - b
        elif op == "*":
            result = a * b
        elif op == "/":
            if b == 0:
                return "错误：除数不能为 0"
            result = a / b
        else:
            return f"错误：不支持的运算符 '{op}'"

        return str(result)
