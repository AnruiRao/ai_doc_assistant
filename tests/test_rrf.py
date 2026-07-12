"""RRF (Reciprocal Rank Fusion) 融合函数测试"""

from unittest.mock import Mock, patch
from retrieval.rrf import rrf_fuse
from tools.rag_tool import RagTool


class TestRrfFuse:
    """测试 rrf_fuse：RRF 融合 + 边界条件 + 去重"""

    def test_empty_ranked_lists(self):
        """空列表 → ([], [])"""
        result = rrf_fuse([])
        assert result == ([], [])

    def test_single_ranked_list(self):
        """单条列表 → 原样返回"""
        ranked_lists = [
            [
                ("doc1", {"source": "a.txt", "chunk_index": 0}),
                ("doc2", {"source": "a.txt", "chunk_index": 1}),
            ]
        ]
        docs, metas = rrf_fuse(ranked_lists)
        assert docs == ["doc1", "doc2"]
        assert metas == [
            {"source": "a.txt", "chunk_index": 0},
            {"source": "a.txt", "chunk_index": 1},
        ]

    def test_all_empty_sub_lists(self):
        """多条空子列表 → ([], [])"""
        result = rrf_fuse([[], []])
        assert result == ([], [])

    def test_rrf_three_lists_consensus_wins(self):
        """文档A在三路都排第1 → 排在首位"""
        list1 = [
            ("docA", {"source": "s1", "chunk_index": 0}),
            ("docB", {"source": "s1", "chunk_index": 1}),
        ]
        list2 = [
            ("docA", {"source": "s1", "chunk_index": 0}),
            ("docC", {"source": "s1", "chunk_index": 2}),
        ]
        list3 = [
            ("docA", {"source": "s1", "chunk_index": 0}),
            ("docD", {"source": "s1", "chunk_index": 3}),
        ]

        docs, metas = rrf_fuse(ranked_lists=[list1, list2, list3], top_k=4)

        assert docs[0] == "docA"
        # A + B + C + D = 4 条
        assert len(docs) == 4

    def test_rrf_top_k_truncation(self):
        """top_k 截断生效"""
        ranked_lists = [
            [
                ("d1", {"source": "s", "chunk_index": 0}),
                ("d2", {"source": "s", "chunk_index": 1}),
                ("d3", {"source": "s", "chunk_index": 2}),
                ("d4", {"source": "s", "chunk_index": 3}),
            ],
            [
                ("d3", {"source": "s", "chunk_index": 2}),
                ("d1", {"source": "s", "chunk_index": 0}),
                ("d4", {"source": "s", "chunk_index": 3}),
                ("d5", {"source": "s", "chunk_index": 4}),
            ],
        ]
        docs, metas = rrf_fuse(ranked_lists=ranked_lists, top_k=2)

        assert len(docs) == 2
        assert len(metas) == 2

    def test_rrf_metadata_preserved(self):
        """metadata 正确保留"""
        meta1 = {"source": "a.txt", "chunk_index": 0, "extra": "info1"}
        meta2 = {"source": "a.txt", "chunk_index": 1, "extra": "info2"}

        ranked_lists = [
            [("doc1", meta1), ("doc2", meta2)],
            [("doc1", meta1)],
        ]
        docs, metas = rrf_fuse(ranked_lists=ranked_lists, top_k=2)

        assert len(docs) == 2
        # metadata 应与首次出现时一致
        assert metas[0] == meta1
        assert metas[1] == meta2

    def test_rrf_mixed_empty_sub_lists(self):
        """部分子列表为空"""
        ranked_lists = [
            [("docA", {"source": "s", "chunk_index": 0})],
            [],
            [("docB", {"source": "s", "chunk_index": 1})],
        ]
        docs, metas = rrf_fuse(ranked_lists=ranked_lists, top_k=2)

        assert len(docs) == 2
        assert "docA" in docs
        assert "docB" in docs

    def test_rrf_doc_only_in_one_list(self):
        """只出现在一条子查询末尾的文档"""
        list1 = [
            ("docA", {"source": "s", "chunk_index": 0}),
            ("docB", {"source": "s", "chunk_index": 1}),
            ("docC", {"source": "s", "chunk_index": 2}),
            ("docD", {"source": "s", "chunk_index": 3}),
            ("docE", {"source": "s", "chunk_index": 4}),
        ]
        list2 = [
            ("docA", {"source": "s", "chunk_index": 0}),
        ]

        docs, metas = rrf_fuse(ranked_lists=[list1, list2], top_k=5)

        # docE 仅出现在 list1 末尾（rank 5），RRF 后 score 为 1/(60+5)
        # 应出现在结果中
        assert "docE" in docs

    def test_rrf_dedup_within_same_list(self):
        """同一子查询内重复文档不计分两次"""
        ranked_lists = [
            [
                ("docA", {"source": "s", "chunk_index": 0}),
                ("docA", {"source": "s", "chunk_index": 0}),  # 重复
                ("docB", {"source": "s", "chunk_index": 1}),
            ],
            [
                ("docA", {"source": "s", "chunk_index": 0}),
                ("docB", {"source": "s", "chunk_index": 1}),
            ],
        ]
        docs, metas = rrf_fuse(ranked_lists=ranked_lists, top_k=3)

        # docA 在第一列表只计 1 次（rank 1）：1/(60+1)，第二列表（rank 1）：1/(60+1)
        #   = 2/61 ≈ 0.03279
        # docB 在第一列表（rank 3）：1/(60+3)，第二列表（rank 2）：1/(60+2)
        #   ≈ 0.01587 + 0.01613 = 0.03200
        # docA 总分更高
        assert docs[0] == "docA"
        assert len(docs) == 2

    def test_rrf_none_metadata(self):
        """metadata 为 None 时正常处理"""
        ranked_lists = [
            [
                ("docA", {"source": "s", "chunk_index": 0}),
                ("docB", None),
            ],
            [
                ("docB", None),
                ("docA", {"source": "s", "chunk_index": 0}),
            ],
        ]
        docs, metas = rrf_fuse(ranked_lists=ranked_lists, top_k=3)

        assert len(docs) == 2
        assert "docA" in docs
        assert "docB" in docs



class TestSearchRawRrf:
    def setup_method(self):
        self.tool = RagTool()
        self.tool._reranker = None
        self.tool._rewrite = None

    def test_search_raw_rrf_called_with_multiple_queries(self):
        """多条子查询 → rrf_fuse 被调用"""
        mock_vs = Mock()
        mock_vs.similarity_search.return_value = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"source": "s", "chunk_index": 0}, {"source": "s", "chunk_index": 1}]],
            "distances": [[0.1, 0.2]],  # 低于阈值 1.0，保留
        }

        mock_rewriter = Mock()
        mock_rewriter.rewrite.return_value = ["子查询1", "子查询2"]
        mock_rrf = Mock(return_value=(["rrf_doc1"], [{"source": "rrf"}]))
        self.tool._rewrite = mock_rewriter

        with (
            patch("tools.rag_tool.VectorStore", return_value=mock_vs),
            patch("tools.rag_tool.rrf_fuse", mock_rrf),
        ):
            docs, metas = self.tool.search_raw(
                query="测试问题", k=10,
                collection_name="test", persist_directory="/tmp/test",
            )

        mock_rrf.assert_called_once()
        assert docs == ["rrf_doc1"]
        assert metas == [{"source": "rrf"}]

    def test_search_raw_no_qr_single_query(self):
        """QR关闭 → 单条子查询 → rrf_fuse 走单列表快路径"""
        mock_vs = Mock()
        mock_vs.similarity_search.return_value = {
            "documents": [["doc1"]],
            "metadatas": [[{"source": "s", "chunk_index": 0}]],
            "distances": [[0.15]],  # 低于阈值 1.0，保留
        }

        self.tool._rewrite = None

        with patch("tools.rag_tool.VectorStore", return_value=mock_vs):
            docs, metas = self.tool.search_raw(
                query="简单问题", k=10,
                collection_name="test", persist_directory="/tmp/test",
            )

        assert docs == ["doc1"]

    def test_search_raw_with_reranker(self):
        """reranker 开启 → 最终结果被截断到 k 条"""
        mock_vs = Mock()
        # recall_k=20, 模拟 20 条文档
        mock_vs.similarity_search.return_value = {
            "documents": [[f"doc{i}" for i in range(20)]],
            "metadatas": [[{"source": "s", "chunk_index": i} for i in range(20)]],
            "distances": [[0.1] * 20],  # 全部低于阈值 1.0，保留
        }

        mock_reranker = Mock()
        mock_reranker.rerank.return_value = [
            (f"doc{i}", round(1.0 - i * 0.05, 2)) for i in range(4)
        ]

        self.tool._rewrite = None  # 单条子查询
        self.tool._reranker = mock_reranker

        with patch("tools.rag_tool.VectorStore", return_value=mock_vs):
            docs, metas = self.tool.search_raw(
                query="测试", k=4,
                collection_name="test", persist_directory="/tmp/test",
            )

        assert len(docs) == 4
        mock_reranker.rerank.assert_called_once()
