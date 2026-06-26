from ingestion.chunker import Chunker


class TestMergeShortChunks:
    """测试 _merge_short_chunks 短段落合并逻辑"""

    def setup_method(self):
        self.chunker = Chunker()
        self.chunk_size = 1000
        self.min_threshold = int(self.chunk_size * 0.4)  # 400

    def test_merge_short_with_big(self):
        """短碎片附到大 chunk 上合并"""
        chunks = [
            "## 短标题",                          # 5字
            "另一行短标题",                         # 5字
            "具体内容" * 200,                       # 600字
            "- 列表项",                             # 4字
            "又一堆内容" * 200,                      # 600字
        ]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) <= 3, f"应合并为更少的 chunk，实际 {len(result)} 个"
        for c in result:
            assert len(c) >= self.min_threshold, f"存在小于 {self.min_threshold} 字的 chunk: {len(c)}"

    def test_all_big_chunks(self):
        """所有 chunk 都已达到最小阈值，无需合并"""
        chunks = ["A" * 500, "B" * 500]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) == 2, "大 chunk 不应被合并"
        assert result[0] == "A" * 500
        assert result[1] == "B" * 500

    def test_tail_residual_merged(self):
        """末尾短碎片合并到前一个 chunk"""
        chunks = [
            "长内容" * 150,    # 450字 ≥ 400
            "短尾巴",           # 3字 < 400
        ]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) == 1, "末尾碎片应合并到前一块"
        assert "短尾巴" in result[0]

    def test_all_short(self):
        """所有 chunk 都短于阈值，应合并为一个 chunk"""
        chunks = ["A" * 100, "B" * 100, "C" * 100]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) == 1, "全短文档应合并成一个 chunk"
        assert "A" in result[0] and "B" in result[0] and "C" in result[0]

    def test_empty_list(self):
        """空列表"""
        result = self.chunker._merge_short_chunks([], self.chunk_size)
        assert result == []

    def test_single_short_chunk(self):
        """单个短 chunk"""
        result = self.chunker._merge_short_chunks(["短"], self.chunk_size)
        assert len(result) == 1
        assert result[0] == "短"

    def test_single_big_chunk(self):
        """单个大 chunk"""
        text = "大" * 500
        result = self.chunker._merge_short_chunks([text], self.chunk_size)
        assert len(result) == 1
        assert result[0] == text

    def test_big_chunk_absorbs_preceding_shorts(self):
        """大 chunk 前的短碎片被吸收，不会单独成块"""
        chunks = [
            "前置短标题",                              # 5字
            "大段落" * 200,                             # 600字
        ]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) == 1
        assert "前置短标题" in result[0]
        assert "大段落" in result[0]

    def test_no_data_loss(self):
        """总字符数不因合并而丢失"""
        raw = ["短" * 50, "中" * 100, "长" * 300]
        total_in = sum(len(c) for c in raw)
        result = self.chunker._merge_short_chunks(raw, self.chunk_size)
        total_out = sum(len(c) for c in result)
        # 合并时加了 "\n\n" 分隔符，总长度只会增加
        assert total_out >= total_in

    def test_chunk_size_soft_constraint(self):
        """短碎片合并可能导致超过 chunk_size，这是可以接受的"""
        chunks = ["S" * 350, "L" * 800]  # 350 + 800 > 1000
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        assert len(result) == 1
        # 350 < 400 不能独自存在，必须合并，即使总长 1150 > 1000
        assert "S" * 350 in result[0]
        assert "L" * 800 in result[0]

    def test_no_overlap_between_chunks(self):
        """各 chunk 不应包含相同内容（buffer 未清空 bug 的回归测试）"""
        # 模拟 009 文档的段落长度分布：小段落逐个累积输出，每个输出只应包含新的段落
        chunks = [
            "A" * 22,      # 短
            "B" * 98,      # 短
            "C" * 5,       # 短
            "D" * 82,      # 短
            "E" * 154,     # 短
            "F" * 107,     # 达阈值 (22+98+5+82+154+107=468 ≥ 400) → 输出
            "G" * 7,       # 重新累积
            "H" * 45,
            "I" * 181,
            "J" * 88,
            "K" * 7,
            "L" * 319,     # 达阈值 (7+45+181+88+7+319=647 ≥ 400) → 输出
            "M" * 5,       # 残余
        ]
        result = self.chunker._merge_short_chunks(chunks, self.chunk_size)
        # 验证：每个 chunk 不应包含前一个 chunk 的内容（buffer 未清空 bug 回归）
        for i in range(1, len(result)):
            assert result[i-1] not in result[i], f"Chunk {i} 包含了 Chunk {i-1} 的内容"
        # 验证：所有原始内容都被保留（\n\n 分隔符导致的差异剔除）
        for original in chunks:
            found = any(original in c for c in result)
            assert found, f"内容块 '{original[:20]}...' 在输出中丢失"

    def test_integration_with_recursive_split(self):
        """集成测试：recursive_split 输出后经合并，不应有短碎片"""
        text = """
## 标题

这是一段较长的具体内容，用来测试递归分割之后的合并效果。
""" + "重复内容。" * 500 + """

## 另一个标题

这里又是一段比较具体的内容描述，确保能够合并。
""" + "更多内容。" * 200
        chunks = self.chunker.recursive_split(text, self.chunk_size)
        for c in chunks:
            assert len(c) >= self.min_threshold, f"存在小于 {self.min_threshold} 字的碎片: {len(c)}字"
