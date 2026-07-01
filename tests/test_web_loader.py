import httpx
import pytest
from ingestion.web_loader import fetch_web_content


class TestFetchWebContent:
    """测试 fetch_web_content 网页内容提取"""

    def test_extract_from_simple_html(self):
        """从带 <div class="content"> 的 HTML 提取文本"""
        html = """
        <html>
          <head><title>测试页面</title></head>
          <body>
            <div class="content">
              <p>重要通知：关于2024年社保缴费基数调整</p>
              <p>各参保单位：</p>
              <ul>
                <li>调整时间：2024年7月1日起</li>
                <li>缴费基数：下限为4200元</li>
              </ul>
            </div>
          </body>
        </html>
        """
        result = fetch_web_content("http://example.com", html=html)
        assert "重要通知" in result
        assert "社保缴费基数调整" in result
        assert "4200元" in result
        # html tag 应被去除
        assert "<div>" not in result
        assert "<p>" not in result

    def test_extract_from_different_content_class(self):
        """从不同 class 名称（article-content）的内容容器提取"""
        html = """
        <html>
          <body>
            <div class="article-content">
              <h1>政务公开指南</h1>
              <p>本指南适用于所有行政机关。</p>
              <p>联系方式：010-12345678</p>
            </div>
            <div class="footer">版权信息</div>
          </body>
        </html>
        """
        result = fetch_web_content("http://example.com", html=html)
        assert "政务公开指南" in result
        assert "010-12345678" in result
        # footer 在内容容器外，不应包含在结果中
        assert "版权信息" not in result

    def test_handles_missing_content(self):
        """没有内容容器时回退到 body 文本"""
        html = """
        <html>
          <body>
            <h1>简单页面</h1>
            <p>这是没有内容容器的页面。</p>
            <p>应该从 body 提取内容。</p>
            &lt;escaped&gt;实体&lt;/escaped&gt;
          </body>
        </html>
        """
        result = fetch_web_content("http://example.com", html=html)
        assert "简单页面" in result
        assert "没有内容容器的页面" in result
        assert "应该从 body 提取内容" in result
        # HTML 实体应被解码
        assert "<escaped>" in result
        assert "实体" in result

    def test_handles_http_error(self):
        """网络错误时抛出异常"""
        with pytest.raises(Exception):
            fetch_web_content("http://192.0.2.1:9999/nonexistent", timeout=1)
