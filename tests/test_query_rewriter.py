from unittest.mock import Mock
from retrieval.query_rewriter import QueryRewriter


class TestQueryRewriter:
    """测试 QueryRewrite：LLM 输出解析 + 兜底逻辑"""

    def setup_method(self):
        self.mock_llm = Mock()

    def test_rewrite_splits_enumerating_query(self):
        """列举型问题 → 拆分为多个子查询"""
        self.mock_llm.invoke.return_value = (
            '{"sub_queries": ["VectorStore 有哪些方法", "VectorStore 如何实现"]}'
        )
        rewriter = QueryRewriter(self.mock_llm)
        result = rewriter.rewrite("VectorStore 有哪些核心方法？")

        assert len(result) == 2
        assert "VectorStore 有哪些方法" in result
        assert "VectorStore 如何实现" in result

    def test_rewrite_no_split_for_simple_query(self):
        """简单事实型问题 → 不拆分，返回 [原query]"""
        self.mock_llm.invoke.return_value = (
            '{"sub_queries": ["为什么选择 Chroma？"]}'
        )
        rewriter = QueryRewriter(self.mock_llm)
        result = rewriter.rewrite("为什么选择 Chroma？")

        assert len(result) == 1
        assert result[0] == "为什么选择 Chroma？"

    def test_rewrite_fallback_on_invalid_json(self):
        """LLM 返回非法 JSON → 兜底返回 [原query]"""
        self.mock_llm.invoke.return_value = "不是 JSON 格式的文本..."
        rewriter = QueryRewriter(self.mock_llm)
        result = rewriter.rewrite("VectorStore 有哪些核心方法？")

        assert result == ["VectorStore 有哪些核心方法？"]

    def test_rewrite_fallback_on_missing_key(self):
        """LLM 返回合法 JSON 但缺少 sub_queries 字段 → 兜底"""
        self.mock_llm.invoke.return_value = '{"other_field": "value"}'
        rewriter = QueryRewriter(self.mock_llm)
        result = rewriter.rewrite("VectorStore 有哪些核心方法？")

        assert result == ["VectorStore 有哪些核心方法？"]

    def test_rewrite_fallback_on_empty_list(self):
        """LLM 返回空 sub_queries → 兜底返回 [原query]"""
        self.mock_llm.invoke.return_value = '{"sub_queries": []}'
        rewriter = QueryRewriter(self.mock_llm)
        result = rewriter.rewrite("VectorStore 有哪些核心方法？")

        assert result == ["VectorStore 有哪些核心方法？"]

    def test_rewrite_passes_query_to_llm(self):
        """验证 query 被传入 LLM 的 user message"""
        self.mock_llm.invoke.return_value = (
            '{"sub_queries": ["测试"]}'
        )
        rewriter = QueryRewriter(self.mock_llm)
        rewriter.rewrite("如何实现缓存？")

        call_args = self.mock_llm.invoke.call_args[0][0]
        user_msg = call_args[1]["content"]
        assert "如何实现缓存？" in user_msg

    def test_rewrite_includes_system_prompt(self):
        """验证 system prompt 包含 rewrite 指令"""
        self.mock_llm.invoke.return_value = (
            '{"sub_queries": ["测试"]}'
        )
        rewriter = QueryRewriter(self.mock_llm)
        rewriter.rewrite("测试问题")

        call_args = self.mock_llm.invoke.call_args[0][0]
        system_msg = call_args[0]["content"]
        assert "列举型" in system_msg
        assert "sub_queries" in system_msg
