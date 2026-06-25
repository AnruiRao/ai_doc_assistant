# 008: Agent 工具参数语义不一致问题（delete 模式的 source vs filename）

- **日期**: 2026-06-25
- **状态**: 已识别，待修复（V3 循环完成后择机回补）

## 背景

`rag_tool` 的 `delete` 模式接受 `source` 参数，底层通过 `VectorStore` 按 `metadata.source` 过滤来定位删除目标。但 `metadata.source` 存储的是**完整文件路径**（格式 `data/uploads/{uuid}_{filename}`），而非用户在对话中认知的原始文件名。

当 Agent 在聊天中收到"删除 xxx.pdf"的指令时，它只知道文件名，不知道带 uuid 前缀的真实路径，于是把 `filename` 当作 `source` 传入 → 匹配不到 → 删除静默失败。

## 根因

**工具参数 schema 与底层数据模型字段语义不一致**：

```
用户认知: filename = "设计文档.pdf"
    ↓ Agent 传参
source = "设计文档.pdf"  ← Chroma metadata.source 存的是 "data/uploads/uuid_设计文档.pdf"
    ↓ 不匹配
删除静默失败
```

这不是代码 bug（代码逻辑正确），而是**参数层抽象泄漏**——把内部存储细节暴露给了 Agent。

## 候选方案

### 方案 1：工具入参对齐用户心智（推荐的优先方案）

把 `delete` 模式的参数从 `source` 改为接受 `filename`，工具内部通过 `DocumentService` 先按 filename 查到完整路径，再执行删除。

- **优点**：Agent 按自然语义传参，无需了解内部存储结构
- **代价**：增加一次服务层查询，但耗时可忽略
- **实现量**：小，修改 `RagToolInput` + `run()` 的 delete 分支

### 方案 2：Prompt 引导两步调用

保留 `source` 参数，但在 `RagToolInput` 的 description 中明确告诉模型："请先用 list 模式查出文档的 source 路径，再将 source 传给 delete 模式"。

- **优点**：零代码改动
- **缺点**：依赖模型严格遵循指令，不够鲁棒；多步调用增加 token 消耗且步骤一多模型容易偏离

### 方案 3：模糊匹配 + 结果确认

delete 分支先按 filename 对 registry 做模糊匹配：

- 命中 0 条 → 告知用户未找到
- 命中 1 条 → 直接删除
- 命中多条 → 返回候选列表，让 Agent 在对话中追问用户确认

- **优点**：用户体验最好，能处理同名文件
- **缺点**：实现最复杂，且需要设计 Agent 与用户的确认交互协议

## 决策

**当前：不实现，保留 TODO。** 理由：

1. **时机不对**：正处于 V3 实测驱动优化的核心阶段，当前瓶颈在 RAG 检索质量（chunk/embedding/rerank），delete 删除属于边缘功能，此时投入产出比低
2. **V3 优先**：V3 的 20 条测试 query 中与删除相关的问题为 0，说明这不是用户实际使用时的痛点
3. **留有空间**：V3 优化过程中可能会引入内容哈希 ID 等变化（见 PLAN.md V3 可选操作清单），删除逻辑届时需要配合调整，现在实现可能很快要重写

**后续计划**：V3 循环收敛后（连续 2-3 轮肉眼无法感知改善），回补此问题，采用**方案 1+3 组合**——工具入参对齐 filename，内部做精确匹配优先 + 模糊匹配兜底，多条命中时返回列表让 Agent 追问。


## 延伸：save 和 delete 模式的实际使用场景已收敛

引入 `DocumentService` 之后，`rag_tool` 的四个模式中有两个的实际入口已经不在聊天框：

| 模式 | 用户实际走哪条路径 | 聊天框 Agent 调用 |
|------|-------------------|-------------------|
| **save** | 侧边栏 `file_uploader` → `routes/documents.py` → `DocumentService.upload()` | ❌ 用户不会在聊天框输入路径让 Agent 读文件 |
| **search** | 聊天框 Agent 调 `rag_tool.search()` | ✅ 核心路径，唯一入口 |
| **delete** | 侧边栏删除按钮 → `DocumentService.delete_by_path()` | ❌ TODO 中，且入口已被侧边栏覆盖 |
| **list** | 聊天框 Agent 调 `rag_tool.list()` | ✅ 独立能力，无替代 |

**save/delete 在聊天框场景下已基本是死代码。** 但暂时不动，理由：

1. **对 V3 检索优化无影响** — search 核心逻辑不动，重构是架构整洁而非功能增益
2. **"未重构但有认知"** — 能解释"为什么当初设计了四个模式"和"为什么现在两个入口迁移了"，比"已经重构完了"更能体现演进式设计思维
3. **等 V4 统一入口策略时一并处理** — 如果 V4 决定让 `rag_tool` 统一调 `DocumentService`（方向 B），那时改比现在单独立项效率高

### 后续计划

V3 循环收敛后，结合 delete TODO 的回补，统一考虑 `rag_tool` 的模式设计：

- **选项 A（收缩）**：去掉 save/delete，只留 search + list，Agent 只管检索，管理操作全走服务层
- **选项 B（统一入口）**：`rag_tool` 所有模式底层都调 `DocumentService`，Agent 统一入口，服务层处理所有持久化细节

倾向于选项 B——让 Agent 可以自然地说"帮我把这个文档存一下"，只是当前阶段的优先级排在检索优化之后。

## 参考

- `src/tools/impl/rag_tool.py` — delete 分支（L94-95），`# TODO: 按名称删除文档功能开发中`
- `src/services/document_service.py` — `delete_by_path()` / `_find_by_filename()` / `_delete_by_record()`
- `docs/decisions/006-tool-system.md` — 工具系统设计决策，含多模式 InputModel 设计
