
import json
from core.config import Settings
from core.llm import BaseLLM

REWRITE_PROMPT = """
    你是一个查询改写助手。判断以下问题是否需要拆分为多个子问题才能完整回答：

    - 列举型（"有哪些"、"包含哪些"、"所有"）→ 拆成 2-4 个子问题
    - 对比型（"区别是什么"、"对比"）→ 拆成 2-3 个子问题
    - 多维度型（"如何设计并实现"、"有哪些步骤，每步做什么"）→ 拆成 2-3 个子问题
    - 简单事实型（"是什么"、"为什么"、单个概念）→ 不拆，原样返回
    - 流程/原理型（"流程是怎样的"、"循环逻辑"、"基本原理"、"怎么工作的"）→ 不拆，答案通常集中在少数 chunk 内

    输出格式：严格的 JSON，格式为 {"sub_queries": ["子问题1", "子问题2"]}
    如果不需要拆分，sub_queries 只包含原问题。
    只输出 JSON，不要加任何解释或前缀。
"""

class QueryRewriter:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    def rewrite(self, query: str) -> list[str]:
        
        message:list[dict] = [
            {"role": "system", "content": REWRITE_PROMPT},
            {"role": "user", "content": f"请改写以下问题：{query}"}
        ]

        result = self.llm.invoke(message)
        try:
            data = json.loads(result)
            sub_queries = data.get("sub_queries", [])
            return sub_queries if sub_queries else [query]
        except (json.JSONDecodeError, KeyError):
            return [query]