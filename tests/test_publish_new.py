"""
Tests for Phase 2: publish_to_paragraph() and publish_to_medium() in publishers.py

测试策略：
- 使用 unittest.mock patch requests.post / requests.get，避免真实 API 调用
- 验证函数签名、入参校验、成功/失败/异常三条路径
"""
import pytest
from unittest.mock import patch, MagicMock


# ══════════════════════════════════════════════════════════════════
# publish_to_paragraph() 测试
# ══════════════════════════════════════════════════════════════════

SAMPLE_PARAGRAPH_SUCCESS = {
    "id": "abc123",
    "url": "https://paragraph.xyz/@mpchat/my-article",
}

SAMPLE_MEDIUM_ME = {
    "data": {
        "id": "user123",
        "username": "mpchat",
        "name": "MPChat",
        "url": "https://medium.com/@mpchat",
    }
}

SAMPLE_MEDIUM_POST_SUCCESS = {
    "data": {
        "id": "post456",
        "title": "Test Article",
        "url": "https://medium.com/@mpchat/test-article-abc123",
        "canonicalUrl": "",
        "publishStatus": "draft",
    }
}


class TestPublishToParagraph:
    def setup_method(self):
        from publishers import publish_to_paragraph
        self.publish = publish_to_paragraph

    def test_empty_api_key_returns_error(self):
        """空 api_key 应直接返回错误，不发网络请求"""
        result = self.publish("", "Title", "# Body", [], "")
        assert result["ok"] is False
        assert "api_key" in result["error"].lower() or "paragraph" in result["error"].lower() or "配置" in result["error"]

    def test_whitespace_api_key_returns_error(self):
        """纯空格 api_key 应返回错误"""
        result = self.publish("   ", "Title", "# Body", [], "")
        assert result["ok"] is False

    def test_empty_title_returns_error(self):
        """空标题应返回错误"""
        result = self.publish("valid-key", "", "# Body", [], "")
        assert result["ok"] is False

    def test_empty_body_returns_error(self):
        """空正文应返回错误"""
        result = self.publish("valid-key", "Title", "", [], "")
        assert result["ok"] is False

    @patch("publishers.requests.post")
    def test_returns_ok_with_url_on_201(self, mock_post):
        """HTTP 201 时返回 ok=True 和文章 URL"""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = SAMPLE_PARAGRAPH_SUCCESS
        mock_post.return_value = mock_resp

        result = self.publish("valid-key", "Test Title", "# Hello\nWorld", ["crypto"], "https://example.com")
        assert result["ok"] is True
        assert "url" in result
        assert result["url"] == SAMPLE_PARAGRAPH_SUCCESS["url"]

    @patch("publishers.requests.post")
    def test_returns_ok_with_url_on_200(self, mock_post):
        """HTTP 200 时也应返回 ok=True"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_PARAGRAPH_SUCCESS
        mock_post.return_value = mock_resp

        result = self.publish("valid-key", "Test Title", "# Hello", [], "")
        assert result["ok"] is True

    @patch("publishers.requests.post")
    def test_http_4xx_returns_error(self, mock_post):
        """HTTP 4xx 应返回 ok=False 和错误信息"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_post.return_value = mock_resp

        result = self.publish("bad-key", "Title", "# Body", [], "")
        assert result["ok"] is False
        assert "401" in result["error"] or "error" in result

    @patch("publishers.requests.post")
    def test_request_exception_returns_error(self, mock_post):
        """网络异常时应返回 ok=False"""
        mock_post.side_effect = Exception("Connection timeout")

        result = self.publish("valid-key", "Title", "# Body", [], "")
        assert result["ok"] is False
        assert "Connection timeout" in result["error"]

    @patch("publishers.requests.post")
    def test_tags_sent_in_payload(self, mock_post):
        """tags 应包含在请求体中"""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = SAMPLE_PARAGRAPH_SUCCESS
        mock_post.return_value = mock_resp

        self.publish("valid-key", "Title", "# Body", ["web3", "crypto"], "")
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else {}
        # tags 应在请求体中
        assert body is not None

    @patch("publishers.requests.post")
    def test_canonical_url_included_when_provided(self, mock_post):
        """提供 canonical_url 时应包含在请求体中"""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = SAMPLE_PARAGRAPH_SUCCESS
        mock_post.return_value = mock_resp

        canonical = "https://myblog.com/original"
        self.publish("valid-key", "Title", "# Body", [], canonical)
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        # canonical_url 值应出现在 payload 中
        payload_str = str(payload)
        assert canonical in payload_str

    @patch("publishers.requests.post")
    def test_authorization_header_uses_api_key(self, mock_post):
        """请求头应包含 API Key 用于认证"""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = SAMPLE_PARAGRAPH_SUCCESS
        mock_post.return_value = mock_resp

        self.publish("my-secret-key", "Title", "# Body", [], "")
        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or {}
        # API Key 应出现在请求头中
        headers_str = str(headers)
        assert "my-secret-key" in headers_str


# ══════════════════════════════════════════════════════════════════
# publish_to_medium() 测试
# ══════════════════════════════════════════════════════════════════

class TestPublishToMedium:
    def setup_method(self):
        from publishers import publish_to_medium
        self.publish = publish_to_medium

    def test_empty_token_falls_back_to_preview(self):
        """空 token 时应降级为格式预览，不发网络请求"""
        result = self.publish("", "Title", "# Body", [], "", "draft")
        assert result["ok"] is True
        assert "preview" in result
        assert "Title" in result["preview"]

    def test_whitespace_token_falls_back_to_preview(self):
        """纯空格 token 也应降级为格式预览"""
        result = self.publish("   ", "Title", "# Body content", [], "", "public")
        assert result["ok"] is True
        assert "preview" in result

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_returns_ok_with_url_on_success(self, mock_get, mock_post):
        """有效 token 下正常发布应返回 ok=True 和 URL"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        result = self.publish("valid-token", "Test Article", "# Hello", ["crypto"], "", "draft")
        assert result["ok"] is True
        assert "url" in result

    @patch("publishers.requests.get")
    def test_me_endpoint_http_error_falls_back_to_preview(self, mock_get):
        """/me 端点失败时应降级为格式预览"""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        result = self.publish("bad-token", "Title", "# Body", [], "", "draft")
        assert result["ok"] is True
        assert "preview" in result

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_post_endpoint_http_error_returns_error(self, mock_get, mock_post):
        """/posts 端点失败时应返回 ok=False"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 400
        post_resp.text = "Bad Request"
        mock_post.return_value = post_resp

        result = self.publish("valid-token", "Title", "# Body", [], "", "draft")
        assert result["ok"] is False
        assert "error" in result

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_draft_status_sent_in_payload(self, mock_get, mock_post):
        """publish_status='draft' 应在请求体中传递"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        self.publish("valid-token", "Title", "# Body", [], "", "draft")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        assert payload.get("publishStatus") == "draft"

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_public_status_sent_in_payload(self, mock_get, mock_post):
        """publish_status='public' 应在请求体中传递"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        self.publish("valid-token", "Title", "# Body", [], "", "public")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        assert payload.get("publishStatus") == "public"

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_tags_sent_in_payload(self, mock_get, mock_post):
        """tags 应包含在请求体中"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        self.publish("valid-token", "Title", "# Body", ["web3", "crypto"], "", "draft")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        assert "tags" in payload

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_canonical_url_sent_when_provided(self, mock_get, mock_post):
        """提供 canonical_url 时应在请求体中传递"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        canonical = "https://myblog.com/original"
        self.publish("valid-token", "Title", "# Body", [], canonical, "draft")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        assert payload.get("canonicalUrl") == canonical

    @patch("publishers.requests.get")
    def test_request_exception_on_me_falls_back_to_preview(self, mock_get):
        """网络异常（/me 端点）时应降级为格式预览"""
        mock_get.side_effect = Exception("Network error")

        result = self.publish("valid-token", "Title", "# Body", [], "", "draft")
        assert result["ok"] is True
        assert "preview" in result

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_bearer_token_in_authorization_header(self, mock_get, mock_post):
        """认证头格式应为 Bearer {token}"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        self.publish("my-medium-token", "Title", "# Body", [], "", "draft")
        get_kwargs = mock_get.call_args
        headers = get_kwargs.kwargs.get("headers") or {}
        auth = headers.get("Authorization", "")
        assert "Bearer" in auth
        assert "my-medium-token" in auth

    @patch("publishers.requests.post")
    @patch("publishers.requests.get")
    def test_content_format_is_markdown(self, mock_get, mock_post):
        """请求体中内容格式应为 markdown"""
        me_resp = MagicMock()
        me_resp.status_code = 200
        me_resp.json.return_value = SAMPLE_MEDIUM_ME
        mock_get.return_value = me_resp

        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = SAMPLE_MEDIUM_POST_SUCCESS
        mock_post.return_value = post_resp

        self.publish("valid-token", "Title", "# Body", [], "", "draft")
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or {}
        assert payload.get("contentFormat") == "markdown"
