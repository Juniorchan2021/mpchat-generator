"""
Tests for api/routers/translate.py 和 external.py 的翻译端点

使用 FastAPI TestClient + mock，不真实调用 LLM。
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


TRANSLATED_EN = "# MPChat: The Future\n\nTranslated content here."
TRANSLATED_TW = "# MPChat：未來\n\n繁體中文翻譯內容。"

VALID_PAYLOAD = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-test-key",
    "base_url": "",
    "article": "# MPChat：加密支付的未来\n\n这是一篇测试文章。",
    "source_lang": "中文",
    "target_lang": "英文",
}


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


# ──────────────────────────────────────────────
# POST /api/v1/translate
# ──────────────────────────────────────────────

class TestTranslateEndpoint:
    @patch("api.routers.translate.translate_article")
    def test_success_returns_200(self, mock_translate, client):
        """正常请求应返回 200 和翻译结果"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/translate", json=VALID_PAYLOAD)
        assert resp.status_code == 200

    @patch("api.routers.translate.translate_article")
    def test_response_schema(self, mock_translate, client):
        """响应体包含 translated_article / source_lang / target_lang"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/translate", json=VALID_PAYLOAD)
        body = resp.json()
        assert "translated_article" in body
        assert "source_lang" in body
        assert "target_lang" in body

    @patch("api.routers.translate.translate_article")
    def test_translated_article_content(self, mock_translate, client):
        """translated_article 的值等于 LLM 返回值"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/translate", json=VALID_PAYLOAD)
        assert resp.json()["translated_article"] == TRANSLATED_EN

    @patch("api.routers.translate.translate_article")
    def test_source_target_lang_echoed(self, mock_translate, client):
        """source_lang / target_lang 与请求一致"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/translate", json=VALID_PAYLOAD)
        body = resp.json()
        assert body["source_lang"] == VALID_PAYLOAD["source_lang"]
        assert body["target_lang"] == VALID_PAYLOAD["target_lang"]

    @patch("api.routers.translate.translate_article")
    def test_translate_called_with_correct_args(self, mock_translate, client):
        """路由应把请求字段正确传给 translate_article()"""
        mock_translate.return_value = TRANSLATED_EN
        client.post("/api/v1/translate", json=VALID_PAYLOAD)
        mock_translate.assert_called_once()
        kwargs = mock_translate.call_args.kwargs
        assert kwargs["provider"] == VALID_PAYLOAD["provider"]
        assert kwargs["api_key"] == VALID_PAYLOAD["api_key"]
        assert kwargs["article"] == VALID_PAYLOAD["article"]
        assert kwargs["source_lang"] == VALID_PAYLOAD["source_lang"]
        assert kwargs["target_lang"] == VALID_PAYLOAD["target_lang"]

    def test_missing_api_key_returns_422(self, client):
        """缺少 api_key 应返回 422"""
        payload = {**VALID_PAYLOAD}
        del payload["api_key"]
        resp = client.post("/api/v1/translate", json=payload)
        assert resp.status_code == 422

    def test_missing_article_returns_422(self, client):
        """缺少 article 应返回 422"""
        payload = {**VALID_PAYLOAD}
        del payload["article"]
        resp = client.post("/api/v1/translate", json=payload)
        assert resp.status_code == 422

    @patch("api.routers.translate.translate_article")
    def test_llm_error_returns_502(self, mock_translate, client):
        """LLM 调用异常应返回 502"""
        mock_translate.side_effect = RuntimeError("LLM unreachable")
        resp = client.post("/api/v1/translate", json=VALID_PAYLOAD)
        assert resp.status_code == 502

    @patch("api.routers.translate.translate_article")
    def test_traditional_chinese_target(self, mock_translate, client):
        """翻译为繁体中文也能正常工作"""
        mock_translate.return_value = TRANSLATED_TW
        payload = {**VALID_PAYLOAD, "target_lang": "繁体中文"}
        resp = client.post("/api/v1/translate", json=payload)
        assert resp.status_code == 200
        assert resp.json()["target_lang"] == "繁体中文"


# ──────────────────────────────────────────────
# POST /api/v1/external/translate
# ──────────────────────────────────────────────

class TestExternalTranslateEndpoint:
    @patch("api.routers.external.translate_article")
    def test_success_returns_200(self, mock_translate, client):
        """外部文章翻译端点正常应返回 200"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/external/translate", json=VALID_PAYLOAD)
        assert resp.status_code == 200

    @patch("api.routers.external.translate_article")
    def test_response_schema(self, mock_translate, client):
        """响应体包含三个必需字段"""
        mock_translate.return_value = TRANSLATED_EN
        resp = client.post("/api/v1/external/translate", json=VALID_PAYLOAD)
        body = resp.json()
        assert "translated_article" in body
        assert "source_lang" in body
        assert "target_lang" in body

    @patch("api.routers.external.translate_article")
    def test_llm_error_returns_502(self, mock_translate, client):
        """LLM 调用异常应返回 502"""
        mock_translate.side_effect = ValueError("empty result")
        resp = client.post("/api/v1/external/translate", json=VALID_PAYLOAD)
        assert resp.status_code == 502

    def test_missing_article_returns_422(self, client):
        """缺少 article 应返回 422"""
        payload = {**VALID_PAYLOAD}
        del payload["article"]
        resp = client.post("/api/v1/external/translate", json=payload)
        assert resp.status_code == 422
