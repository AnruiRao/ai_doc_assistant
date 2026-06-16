# 006: 工具系统设计

- **日期**: 2026-06-17
- **状态**: 已实施，V4 扩展 @tool 装饰器

## 背景

Agent 需要调用外部工具（搜索、计算、RAG 等），需要设计工具的定义和注册方式。

## 当前实现

两层设计：

1. **`Tool` 抽象基类**（`src/tools/base.py`）：继承 + 实现 `run()` 方法
2. **`ToolRegistry` 注册器**（`src/tools/registry.py`）：管理工具的注册、查找、注销

工具定义方式：

```python
class CalculatorTool(Tool):
    def __init__(self):
        super().__init__(name="calculator", description="计算表达式", input_model=CalcInput)

    def run(self, **kwargs) -> str:
        validated = self.input_model(**kwargs)
        return str(eval(validated.expression))
```

## 为什么不用 @tool 装饰器

参考 PLAN.md 的策略：核心逻辑自实现，不依赖框架语法糖。

当前方式的好处：
1. **显式理解**：`to_openai_tool()` 生成 schema 的过程是手写的，开发者能看到 tool schema 长什么样
2. **类型清晰**：通过 `input_model`（Pydantic）把输入校验和 schema 生成合二为一
3. **面试可讲**：可以说"我知道 LangChain 的 @tool 装饰器本质上也是解析函数签名 + 类型注解 → Pydantic schema，我手写的版本是同一件事"

## 后续计划

- **V4**：在 `src/tools/decorator.py` 自实现 `@tool` 装饰器，展示语法糖与基类继承的对比

## 参考

- [OpenAI Function Calling 文档](https://platform.openai.com/docs/guides/function-calling)
