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
| 006 | [V2 异常体系设计](006-v2-exception-hierarchy.md) | 已实施 |
| 007 | [FastAPI + 异步桥接方案](007-fastapi-async-bridge.md) | 已实施 |
| 008 | [V3 滑动窗口上下文](008-sliding-window-context.md) | 已实施 |
| 009 | [Chunker 短段落合并策略](009-chunk-fragmentation-merge.md) | 已实施 |
| 010 | [Embedding 模型升级（V3 评测驱动）](010-embedding-upgrade-v3.md) | 已实施 |
| 011 | [Query Rewrite — LLM 查询改写（V3 实验 A1）](011-query-rewrite.md) | 已实施（默认关） |
| 012 | [Reranker 选型 — 交叉编码器精排（V3 实验 A2）](012-reranker-selection.md) | 已实施 |
| 013 | [RRF 轻量融合](013-rrf-lightweight.md) | 已实施（默认关） |
| — | [垂直领域 Phase A 设计文档](../superpowers/specs/2026-07-01-gov-domain-phase-a.md) | 已实施 |

## 规范

- 新决策在实施前或实施后一周内记录
- 每个文件中 `状态` 字段记录当前阶段（已实施 / 计划中 / 已废弃）
- `后续计划` 字段链接到 PLAN.md 的对应阶段
