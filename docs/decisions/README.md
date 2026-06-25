# 技术决策记录

该目录记录了项目中的关键架构决策（Architecture Decision Records）。

## 格式

每条记录包含：背景、选项、决策理由、后续计划、参考来源。

## 索引

| # | 决策 | 状态 |
|---|---|---|
| 001 | [Embedding 模型选型](001-embedding-model.md) | 已实施 |
| 002 | [文本分块策略](002-chunk-strategy.md) | 已实施 |
| 003 | [向量库选型](003-vector-store.md) | 已实施 |
| 004 | [LLM 供应商和 API 协议](004-llm-provider.md) | 已实施 |
| 005 | [Agent 模式选型](005-agent-pattern.md) | 已实施 |
| 006 | [工具系统设计](006-tool-system.md) | 已实施 |
| 007 | [FastAPI + 异步桥接架构](007-fastapi-async.md) | 已实施 |
| 008 | [Agent 工具参数语义不一致问题](008-tool-parameter-semantic-mismatch.md) | 已识别，待修复 |

## 规范

- 新决策在实施前或实施后一周内记录
- 每个文件中 `状态` 字段记录当前阶段（已实施 / 计划中 / 已废弃）
- `后续计划` 字段链接到 PLAN.md 的对应阶段
