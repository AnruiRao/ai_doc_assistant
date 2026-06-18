# 005: Agent 模式选型

- **日期**: 2026-06-17
- **状态**: 已实施

## 背景

需要选择 Agent 的实现模式。

## 选项

| 方案 | 复杂度 | 可控性 | 学习价值 |
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

1. **核心价值**：能讲清 ReAct 每个环节做了什么，而非"LangChain 帮我做了"
2. **完全可控**：prompt、tool_calls 流程、错误处理全部自己控制
3. **调试容易**：出问题时能精确定位到循环中的哪一步

对比 LangChain 的实现：
- LangChain AgentExecutor 本质也是 ReAct 循环，只是封装了 callback、parser 等
- 但出问题时需要理解它内部的 AgentExecutor 状态机，调试门槛更高

## 后续计划

- **V4**：引入 LangChain / LangGraph 适配层，对比自实现和框架方案的差异

---

## 当前 Agent 能力边界

### Tool Selection 策略

当前通过 `tool_calls[].name` 与 `registry.get_tool(name)` 精确匹配。LLM 返回的 function name 必须在 registry 中注册过，否则 `get_tool` 返回 None。这是最简单的精确匹配策略，不做模糊匹配或相似度路由。

后续演进：
- **V3**：加入 Tool 描述相似度 fallback，当精确匹配不到时尝试语义搜索工具描述
- **V4**：支持 Tool 分组 + 权限控制，不同场景暴露不同工具集

### Memory 策略

当前是**全历史保留**：每次对话将全部 `session_state.messages` 传给 LLM。不做总结截断，不区分短期/长期记忆。

注意：
- 优点是实现简单，上下文完整
- 缺点是 token 消耗随轮次线性增长，长对话 cost 高
- V2-ChatService 提供 session 管理能力，但 memory 压缩策略留到 V4（引入 Redis 时一并实现）

### 循环终止条件

```
while steps < max_steps:
    response = llm.invoke_with_tools(messages, tools)
    if response.tool_calls:
        for each tool_call:
            execute → append result
        steps += 1
        continue
    else:
        return response.content  # 无 tool_calls → 终止
raise AgentError("max_steps 超限")  # 超限 → 异常
```

两个终止信号：
1. **正常终止**：LLM 返回的内容中没有 `tool_calls` → 视为最终回答
2. **异常终止**：循环次数达到 `max_steps`（当前 V1 写死 10 次）→ 抛 `AgentError`

不支持的终止模式（V4 后考虑）：
- Token 预算终止（到量截断返回已有内容）
- 置信度终止（LLM 返回低 confidence 时提前退出）
- 用户主动中断

### Tool 执行方式

Tool 的 `run()` 是同步方法。V1 中 Agent 同步顺序执行所有 tool_calls（一个返回结果后再调下一个）。V2 异步化后通过 `asyncio.to_thread()` 桥接，但 Tool 本身仍是同步函数。

不支持的执行模式（V4 后考虑）：
- 并行 Tool 执行（多个独立 tool_calls 同时执行）
- 流式 Tool 执行（Tool 边计算边返回中间结果）

---

## 参考

- ReAct: Synergizing Reasoning and Acting in Language Models (arXiv:2210.03629)
- LangChain AgentExecutor 源码
