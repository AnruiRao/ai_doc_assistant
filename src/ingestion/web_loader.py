import re
import html as html_mod

import httpx


_CONTENT_SELECTORS = [
    'class="content"',
    'class="article-content"',
    'id="content"',
    'class="main"',
    'class="text"',
    'class="article"',
]


def _extract_content_area(raw: str) -> str:
    """从 HTML 中提取正文区域。

    优先查找常见内容容器（div with content/article-content 等 class 或 id），
    如果找不到则回退到 <body> 内容，最后回退到完整 HTML。
    """
    # 尝试查找内容容器
    for selector in _CONTENT_SELECTORS:
        attr_pattern = selector.replace('"', "['\"]")
        pattern = re.compile(
            rf'<(div|section|main|article)\s+{attr_pattern}[^>]*>(.*?)</\1>',
            re.DOTALL | re.IGNORECASE,
        )
        match = pattern.search(raw)
        if match:
            return match.group(2)

    # 回退到 body
    body_match = re.search(
        r'<body[^>]*>(.*?)</body>',
        raw,
        re.DOTALL | re.IGNORECASE,
    )
    if body_match:
        return body_match.group(1)

    # 最后回退到完整 HTML
    return raw


def _strip_tags(text: str) -> str:
    """去除 HTML 标签，替换为换行符。"""
    return re.sub(r'<[^>]+>', '\n', text, flags=re.DOTALL)


def _decode_entities(text: str) -> str:
    """解码 HTML 实体。"""
    return html_mod.unescape(text)


def _collapse_blank_lines(text: str) -> str:
    """压缩多余空行（3+ 连续换行 -> 2），去除纯空白行。"""
    # 将连续 3 个以上换行符替换为 2 个
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除纯空白行（仅由空白字符组成的行）
    lines = [line for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def fetch_web_content(url: str, html: str | None = None, timeout: int = 30) -> str:
    """从政务网页 URL 提取结构化文本内容。

    Args:
        url: 网页地址。
        html: 可选的 HTML 字符串（用于测试注入，不提供则从 url 获取）。
        timeout: HTTP 超时秒数。

    Returns:
        提取并清理后的纯文本内容。
    """
    if html is None:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GovDocBot/1.0)"},
        )
        response.raise_for_status()
        html = response.text

    # 清理 <script> 和 <style> 内容
    html = re.sub(
        r'<(script|style)[^>]*>.*?</\1>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    content = _extract_content_area(html)
    content = _strip_tags(content)
    content = _decode_entities(content)
    content = _collapse_blank_lines(content)

    return content
