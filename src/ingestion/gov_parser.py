"""政务办事指南章节识别与标记。

提供 tag_gov_sections() 函数，用于在数据处理链的 cleaner 和 chunker
之间识别政务文档的章节边界并插入标记。
"""

import re

SECTION_KEYWORDS: dict[str, list[str]] = {
    "设定依据": ["设定依据", "法律依据", "法规依据", "审批依据"],
    "申请条件": ["申请条件", "受理条件", "适用条件"],
    "办理材料": ["办理材料", "申请材料", "提交材料", "材料清单", "申请材料目录"],
    "办理流程": ["办理流程", "办理程序", "审批流程", "办理基本流程"],
    "办理时限": ["办理时限", "承诺时限", "法定期限", "办结时限"],
    "受理机构": ["受理机构", "办理地点", "办理机构"],
    "收费标准": ["收费标准", "收费依据"],
    "结果送达": ["结果送达"],
    "咨询方式": ["咨询途径", "咨询方式"],
}

# 扁平化章节关键词，按长度降序排列以避免短词先匹配截断长词匹配
_ALL_KEYWORDS: list[tuple[str, str]] = sorted(
    [(cname, kw) for cname, kws in SECTION_KEYWORDS.items() for kw in kws],
    key=lambda x: -len(x[1]),
)

# 匹配命名章节标题：整行精确匹配关键词
_NAMED_PATTERN = re.compile(
    r"^(" + "|".join(re.escape(kw) for _, kw in _ALL_KEYWORDS) + r")$",
    re.MULTILINE,
)


def tag_gov_sections(text: str) -> str:
    """识别政务文档的章节边界并插入标记。

    处理步骤：
    1. 识别中文数字编号章节（一、二、三…），在前面插入 \n\n 段落分隔
    2. 识别命名章节标题（设定依据、办理材料等），在标题前加 【章节名】 标记
    3. 保持数字列表（1. 2. 3.）完整不截断

    Args:
        text: 经过 clean_text 处理后的纯文本。

    Returns:
        标记了章节边界的文本。
    """
    if not text:
        return ""

    # 处理 \r\n 行尾，确保正则匹配正常
    text = text.replace('\r\n', '\n')

    # 1. 识别中文数字编号章节：在编号标题前插入段落分隔（但保留已有分隔）
    #    匹配不在段首（即前面不是空行或文本开头）的编号行
    text = re.sub(
        r'(?<=\S)\n(?=[一二三四五六七八九十百千]+、)',
        '\n\n',
        text,
    )

    # 2. 识别命名章节标题：整行匹配关键词，加 【章节名】 标记
    def _mark_named(match: re.Match) -> str:
        keyword = match.group(1)
        section_name = _find_section_name(keyword)
        return f"【{section_name}】\n{keyword}"

    text = _NAMED_PATTERN.sub(_mark_named, text)

    # 3. 整理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _find_section_name(keyword: str) -> str:
    """根据关键词查找对应的章节名称。"""
    for name, keywords in SECTION_KEYWORDS.items():
        if keyword in keywords:
            return name
    return keyword  # fallback（不应发生）
