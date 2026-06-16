# 005: Agent 模式选型

- **日期**: 2026-06-17
- **状态**: 已实施

## 背景

需要选择 Agent 的实现模式。这是项目的核心面试亮点。

## 选项

| 方案 | 复杂度 | 可控性 | 面试价值 |
|---|---|---|---|
| 自实现 ReAct | 中 | 高 | 高 |
| LangChain AgentExecutor | 低 | 低 | 低（只会用框架） |
| LangGraph | 中高 | 中 | 中（V4 可以展示） |

## 决策

**V1-V3 自实现 ReAct 循环**（如 PLAN.md 所定义）：

```
while steps < max_steps:
    # 1. LLM 推理（带工具定义）
    response = llm.invoke_with_tools(messages, tools)
    # 2. 检测是否需要调用工具
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool = registry.get_tool(tool_call.name)
            result = tool.run(**tool_call.args)
            messages.append(tool_result)
        continue
    # 3. 否则作为最终回答返回
    return response.content
```

理由：

1. **面试核心竞争力**：能讲清 ReAct 每个环节做了什么，而非"LangChain 帮我做了"
2. **完全可控**：prompt、tool_calls 流程、错误处理全部自己控制
3. **调试容易**：出问题时能精确定位到循环中的哪一步

对比 LangChain 的实现：
- LangChain AgentExecutor 本质也是 ReAct 循环，只是封装了 callback、parser 等
- 但出问题时需要理解它内部的 AgentExecutor 状态机，调试门槛更高

## 后续计划

- **V4**：引入 LangChain / LangGraph 适配层，对比自实现和框架方案的差异

## 参考

- ReAct: Synergizing Reasoning and Acting in Language Models (arXiv:2210.03629)
- LangChain AgentExecutor 源码
