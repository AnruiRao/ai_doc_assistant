from ingestion.gov_parser import tag_gov_sections


class TestTagGovSections:
    """测试 tag_gov_sections 章节识别标记"""

    def test_empty_text(self):
        """空文本返回空字符串"""
        assert tag_gov_sections("") == ""

    def test_no_match(self):
        """无章节标记的普通文本不变"""
        text = "今天天气很好。\n\n我们去公园散步。"
        assert tag_gov_sections(text) == text

    def test_numbered_sections(self):
        """一、二、三编号章节识别并在前面加 \n\n"""
        text = (
            "第一章 总则\n"
            "一、适用范围\n"
            "本规定适用于本市所有企业。\n"
            "二、登记程序\n"
            "企业应当按流程办理。\n"
            "三、监督管理\n"
            "相关部门负责监督。"
        )
        result = tag_gov_sections(text)
        lines = result.split("\n\n")
        # 应该有 4 段：开头 + 3 章节
        assert len(lines) >= 4, f"应 split 出至少 4 段，实际 {len(lines)}"
        # 检查编号行本身被保留
        assert any("一、适用范围" in l for l in lines)
        assert any("二、登记程序" in l for l in lines)
        assert any("三、监督管理" in l for l in lines)

    def test_named_sections(self):
        """命名章节（办理材料等）加 【】 标记"""
        text = (
            "申请条件\n"
            "申请人应当年满18周岁。\n"
            "办理材料\n"
            "1. 身份证复印件\n"
            "2. 申请表\n"
            "办理时限\n"
            "15个工作日。"
        )
        result = tag_gov_sections(text)
        assert "【申请条件】" in result
        assert "【办理材料】" in result
        assert "【办理时限】" in result
        # 原始行文本也被保留（不带【】）
        assert "申请条件" in result
        assert "办理材料" in result
        assert "办理时限" in result

    def test_mixed_sections(self):
        """编号章节 + 命名章节混合"""
        text = (
            "一、设定依据\n"
            "依据《行政许可法》。\n"
            "二、申请条件\n"
            "年满18周岁。\n"
            "办理材料\n"
            "身份证。"
        )
        result = tag_gov_sections(text)
        parts = result.split("\n\n")
        # 编号和命名标记都应生效
        assert any("一、设定依据" in l for l in parts)
        assert any("二、申请条件" in l for l in parts)
        assert "【办理材料】" in result

    def test_preserves_list(self):
        """数字列表保持完整"""
        text = (
            "请提交以下材料：\n"
            "1. 身份证原件及复印件\n"
            "2. 户口本原件及复印件\n"
            "3. 近期免冠照片2张\n"
            "以上材料均需一式一份。"
        )
        result = tag_gov_sections(text)
        # 数字列表应保持不变
        assert "1. 身份证原件及复印件" in result
        assert "2. 户口本原件及复印件" in result
        assert "3. 近期免冠照片2张" in result
        # 不应被截断
        assert "以上材料均需一式一份" in result

    def test_no_false_positive_for_common_words(self):
        """正文中出现的关键词不会误标记"""
        text = (
            "在办理材料审核过程中，工作人员应当认真核对。\n"
            "如果超过办理时限，需要提交延期说明。\n"
            "有关申请条件的问题，请咨询办理机构。"
        )
        result = tag_gov_sections(text)
        # 不应插入章节标记（关键词在句子中间不是章节标题）
        assert "【办理材料】" not in result
        assert "【办理时限】" not in result
        assert "【申请条件】" not in result
        assert "【受理机构】" not in result
        # 原文应完整保留
        assert "在办理材料审核过程中" in result
        assert "如果超过办理时限" in result
        assert "有关申请条件的问题" in result
