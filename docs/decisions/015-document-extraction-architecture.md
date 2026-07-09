# 015: 文档提取架构重构 — 可插拔提取器策略链

- **日期**: 2026-07-09
- **状态**: 待讨论

## 背景

当前 `src/ingestion/web_loader.py` 使用正则表达式匹配 HTML，仅支持 7 个硬编码的内容容器选择器（`class="content"`、`id="main"` 等），遇到不同结构的页面直接退化到整页 `<body>`。

问题本质：**提取逻辑与特定页面结构耦合，缺乏适配不同网站的扩展能力。** 政府网站页面结构千差万别，单一策略无法覆盖。

## 已有讨论（待确认）

### 核心思路：策略模式 + 管道模式

将单块的提取函数拆分为可插拔的提取器链：

```
原始 HTML → 提取器链遍历 → 第一个匹配的提取器 → 提取结果
                         ↓
                  无匹配 → Readability 通用提取
                         ↓
                  还不行 → GenericFallback 兜底
```

### 三层提取器

| 提取器 | 策略 | 适用场景 |
|--------|------|---------|
| GovSiteExtractor | 精确 CSS 选择器，按 hostname 匹配 | 已知的常用政府网站 |
| ReadabilityExtractor | Mozilla Readability 算法分析正文密度 | 未知的通用文章页 |
| GenericFallbackExtractor | DOM 解析 + 文本密度兜底 | 所有策略都失败时 |

### 约束

- 不改变外部接口（`fetch_web_content()` 签名和返回值不变）
- 不引入无头浏览器
- 不处理 robots.txt
- 保留纯文本输出（不做 Markdown）
- 不改变下游管道（`cleaner()` → `gov_parser()` → `chunker()`）

---

**以下为待讨论内容，将在后续对话中确认后补充。**

## 技术选型（待讨论）

<!--
候选方向：
1. readability-lxml (Mozilla Readability Python 移植)
2. trafilatura (专门针对新闻/文章提取)
3. lxml + 自实现 HTML 密度分析
4. BeautifulSoup + cssselect
-->

## 提取器链编排（待讨论）

<!--
- 优先级顺序
- 配置方式（代码 vs YAML vs 数据库）
- 站点配置注册方式
-->

## 涉及文件（待确认）

| 文件 | 改动 |
|------|------|
| `src/ingestion/web_loader.py` | 替换为策略链入口 |
| `src/ingestion/extractors/base.py` | **新增**，`PageExtractor` 抽象基类 |
| `src/ingestion/extractors/__init__.py` | **新增**，提取器注册 |
| - | 其他待定 |

## 测试策略（待讨论）

<!--
- 引入真实 HTML fixture 替代当前 mock 写法
- 每个提取器独立测试
- 集成测试：给定已知 HTML 输出 → 验证提取结果是否符合预期
-->

## 后续计划

1. 待决策 014 客户端分割实施完成后启动
2. 实施后更新 `PLAN.md`/`TASKS.md`
3. 完成后进入 Phase B（引导式导办对话）
