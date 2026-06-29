from unittest.mock import MagicMock
from retrieval.reranker import Reranker


class TestReranker:
    """测试 Reranker：排序逻辑 + 边界条件 + 懒加载"""

    def test_rerank_sorts_by_score_descending(self):
        """验证 rerank 按分数降序排列"""
        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.1, 0.9, 0.5]
        reranker._model = mock_model

        result = reranker.rerank(query="test", documents=["坏", "好", "中", "较差"], top_k=3)

        assert result[0] == ("好", 0.9)
        assert result[1] == ("中", 0.5)
        assert result[2] == ("坏", 0.1)

    def test_rerank_top_k_truncation(self):
        """验证 top_k 截断只返回需要的条数"""
        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.1, 0.9, 0.5, 0.3, 0.8]
        reranker._model = mock_model

        result = reranker.rerank(query="test", documents=["a", "b", "c", "d", "e"], top_k=2)

        assert len(result) == 2
        assert result[0][0] == "b"  # 0.9
        assert result[1][0] == "e"  # 0.8

    def test_rerank_empty_documents(self):
        """空文档列表 → 返回空列表"""
        reranker = Reranker()
        result = reranker.rerank(query="test", documents=[], top_k=4)
        assert result == []

    def test_rerank_fewer_docs_than_top_k(self):
        """文档数 < top_k 时 → 原序返回 0.0 分，不调用 predict"""
        reranker = Reranker()
        mock_model = MagicMock()
        reranker._model = mock_model

        result = reranker.rerank(query="test", documents=["只有两条"], top_k=5)

        assert len(result) == 1
        assert result[0] == ("只有两条", 0.0)
        mock_model.predict.assert_not_called()

    def test_rerank_exactly_top_k(self):
        """文档数 == top_k 时 → 原序返回 0.0 分，不调用 predict"""
        reranker = Reranker()
        mock_model = MagicMock()
        reranker._model = mock_model

        result = reranker.rerank(query="test", documents=["a", "b", "c"], top_k=3)

        assert len(result) == 3
        assert result[0] == ("a", 0.0)
        assert result[1] == ("b", 0.0)
        assert result[2] == ("c", 0.0)
        mock_model.predict.assert_not_called()

    def test_rerank_model_is_lazy(self):
        """验证模型在 __init__ 时未加载，首次 rerank 时才初始化"""
        reranker = Reranker()
        assert reranker._model is None  # 尚未加载

    def test_rerank_passes_correct_query_doc_pairs(self):
        """验证传给 predict 的 pair 格式为 [(query, doc), ...]"""
        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.5]
        reranker._model = mock_model

        reranker.rerank(query="我的查询", documents=["doc1", "doc2", "doc3"], top_k=2)

        mock_model.predict.assert_called_once()
        pairs_arg = mock_model.predict.call_args[0][0]
        assert pairs_arg == [("我的查询", "doc1"), ("我的查询", "doc2"), ("我的查询", "doc3")]

    def test_rerank_single_document(self):
        """单文档 → 直接返回 0.0 分，不调用 predict"""
        reranker = Reranker()
        mock_model = MagicMock()
        reranker._model = mock_model

        result = reranker.rerank(query="test", documents=["唯一文档"], top_k=4)

        assert len(result) == 1
        assert result[0] == ("唯一文档", 0.0)
        mock_model.predict.assert_not_called()
