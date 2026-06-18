# 004: LLM 供应商和 API 协议

- **日期**: 2026-06-17
- **状态**: 已实施

## 背景

项目需要选择一个 LLM 供应商作为后端推理引擎。

## 选项

| 方案 | API 协议 | 模型 | 成本 |
|---|---|---|---|
| 通义千问 (DashScope) | OpenAI 兼容 | Qwen 系列 | 便宜 |
| OpenAI | OpenAI 原生 | GPT 系列 | 较贵 |
| Anthropic | Anthropic 原生 | Claude 系列 | 较贵 |

## 决策

**选用 OpenAI 兼容协议 + 通义千问 DashScope**，核心决策：

1. **协议选型**：OpenAI 兼容协议。原因：
   - 通用生态，国产模型（千问、智谱、DeepSeek）都支持
   - 最大就业市场，大部分企业用 OpenAI 协议
   - 方便切换（换 base_url 就能换模型）

2. **供应商选型**：通义千问 DashScope。原因：
   - 模型质量好（Qwen 系列持续更新）
   - 有免费额度
   - 支持 OpenAI 兼容格式

3. **SDK 选型**：OpenAI Python SDK。原因：
   - 协议兼容，不需要额外依赖
   - 文档丰富，生态完善
   - 对比使用 dashscope SDK，"用 OpenAI SDK 调千问"展示了协议理解

## 实现方式

`BaseLLM` 类（`src/core/llm.py`）使用 `OpenAI` 客户端，通过环境变量配置：

- `LLM_API_KEY`：DashScope API Key
- `LLM_BASE_URL`：DashScope 兼容端点
- `LLM_MODEL`：默认 `deepseek-v3`
- `DEFAULT_PROVIDER = "qwen"` 标识当前供应商

## 后续计划

- **模型路由（V3+）**：简单任务用小模型（Qwen3-8B），复杂任务用大模型
- **切换测试**：验证换到 DeepSeek / OpenAI 只需改环境变量

## 参考

- [DashScope OpenAI 兼容模式文档](https://help.aliyun.com/zh/model-studio/developer-reference/use-openai-compatible-mode)
