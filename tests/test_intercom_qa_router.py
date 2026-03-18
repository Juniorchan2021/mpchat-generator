"""
Tests for api/routers/intercom_qa.py

使用 FastAPI TestClient + mock，不真实调用 LLM 或 Intercom API。
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


SAMPLE_QA_BY_LANGUAGE = {
    "zh": [
        {"question": "如何发送 USDC？", "answer": "打开 MPChat，点击发送按钮。", "category": "Payments"},
        {"question": "什么是 MPChat？", "answer": "MPChat 是一款加密钱包。", "category": "General"},
    ],
    "zh-TW": [
        {"question": "如何傳送 USDC？", "answer": "開啟 MPChat，點擊傳送按鈕。", "category": "Payments"},
        {"question": "什麼是 MPChat？", "answer": "MPChat 是一款加密錢包。", "category": "General"},
    ],
    "en": [
        {"question": "How do I send USDC?", "answer": "Open MPChat and tap Send.", "category": "Payments"},
        {"question": "What is MPChat?", "answer": "MPChat is a crypto wallet.", "category": "General"},
    ],
}

VALID_GENERATE_PAYLOAD = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-test-key",
    "base_url": "",
    "feature_description": "Users can send and receive USDC stablecoin payments.",
    "product_name": "MPChat",
    "tone": "friendly",
    "count": 5,
    "languages": ["zh", "zh-TW", "en"],
}

VALID_UPLOAD_PAYLOAD = {
    "intercom_token": "intercom-test-token",
    "collection_id": "col-123",
    "title": "How to send USDC?",
    "body": "Open MPChat and tap Send button. Enter recipient address and confirm.",
    "locale": "en",
}


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


# ──────────────────────────────────────────────
# POST /api/v1/intercom/generate-qa
# ──────────────────────────────────────────────

class TestGenerateQAEndpoint:
    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_success_returns_200(self, mock_gen, client):
        """正常请求应返回 200"""
        mock_gen.return_value = SAMPLE_QA_BY_LANGUAGE
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        assert resp.status_code == 200

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_response_schema(self, mock_gen, client):
        """响应体包含 qa_by_language / languages / count_per_language"""
        mock_gen.return_value = SAMPLE_QA_BY_LANGUAGE
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        body = resp.json()
        assert "qa_by_language" in body
        assert "languages" in body
        assert "count_per_language" in body

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_all_languages_present(self, mock_gen, client):
        """响应中应包含所有请求的语言 key"""
        mock_gen.return_value = SAMPLE_QA_BY_LANGUAGE
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        body = resp.json()
        assert "zh" in body["qa_by_language"]
        assert "zh-TW" in body["qa_by_language"]
        assert "en" in body["qa_by_language"]

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_count_per_language_correct(self, mock_gen, client):
        """count_per_language 应与各语言实际列表长度一致"""
        mock_gen.return_value = SAMPLE_QA_BY_LANGUAGE
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        body = resp.json()
        for lang, pairs in body["qa_by_language"].items():
            assert body["count_per_language"][lang] == len(pairs)

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_qa_content_correct(self, mock_gen, client):
        """zh QA 内容应与 mock 返回一致"""
        mock_gen.return_value = SAMPLE_QA_BY_LANGUAGE
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        body = resp.json()
        assert body["qa_by_language"]["zh"][0]["question"] == "如何发送 USDC？"

    def test_missing_api_key_returns_422(self, client):
        """缺少 api_key 应返回 422"""
        payload = {**VALID_GENERATE_PAYLOAD}
        del payload["api_key"]
        resp = client.post("/api/v1/intercom/generate-qa", json=payload)
        assert resp.status_code == 422

    def test_missing_feature_description_returns_422(self, client):
        """缺少 feature_description 应返回 422"""
        payload = {**VALID_GENERATE_PAYLOAD}
        del payload["feature_description"]
        resp = client.post("/api/v1/intercom/generate-qa", json=payload)
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_value_error_returns_422(self, mock_gen, client):
        """业务层 ValueError 应映射为 422"""
        mock_gen.side_effect = ValueError("feature_description 不能为空")
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_llm_error_returns_502(self, mock_gen, client):
        """LLM 调用异常应映射为 502"""
        mock_gen.side_effect = Exception("LLM timeout")
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        assert resp.status_code == 502

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_empty_result_returns_200(self, mock_gen, client):
        """LLM 返回空字典时应正常返回 200"""
        mock_gen.return_value = {"zh": [], "zh-TW": [], "en": []}
        resp = client.post("/api/v1/intercom/generate-qa", json=VALID_GENERATE_PAYLOAD)
        assert resp.status_code == 200
        body = resp.json()
        assert body["qa_by_language"]["zh"] == []

    @patch("api.routers.intercom_qa.generate_qa_pairs")
    def test_languages_field_echoed_back(self, mock_gen, client):
        """响应中 languages 字段应与请求一致"""
        mock_gen.return_value = {"zh": [], "en": []}
        payload = {**VALID_GENERATE_PAYLOAD, "languages": ["zh", "en"]}
        resp = client.post("/api/v1/intercom/generate-qa", json=payload)
        assert resp.status_code == 200
        assert set(resp.json()["languages"]) == {"zh", "en"}


# ──────────────────────────────────────────────
# POST /api/v1/intercom/upload
# ──────────────────────────────────────────────

class TestUploadEndpoint:
    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_success_returns_200(self, mock_upload, client):
        """成功上传应返回 200"""
        mock_upload.return_value = {"id": "art-999", "title": "How to send USDC?"}
        resp = client.post("/api/v1/intercom/upload", json=VALID_UPLOAD_PAYLOAD)
        assert resp.status_code == 200

    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_response_contains_ok_true(self, mock_upload, client):
        """成功响应应包含 ok: true"""
        mock_upload.return_value = {"id": "art-999"}
        resp = client.post("/api/v1/intercom/upload", json=VALID_UPLOAD_PAYLOAD)
        body = resp.json()
        assert body.get("ok") is True

    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_response_contains_article_id(self, mock_upload, client):
        """响应应包含 Intercom 返回的文章 ID"""
        mock_upload.return_value = {"id": "art-999"}
        resp = client.post("/api/v1/intercom/upload", json=VALID_UPLOAD_PAYLOAD)
        body = resp.json()
        assert body.get("article_id") == "art-999"

    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_locale_passed_to_core(self, mock_upload, client):
        """locale 参数应传递给核心函数"""
        mock_upload.return_value = {"id": "x"}
        payload = {**VALID_UPLOAD_PAYLOAD, "locale": "zh-TW"}
        resp = client.post("/api/v1/intercom/upload", json=payload)
        assert resp.status_code == 200
        call_kwargs = mock_upload.call_args
        assert call_kwargs.kwargs.get("locale") == "zh-TW" or "zh-TW" in str(call_kwargs)

    def test_missing_intercom_token_returns_422(self, client):
        """缺少 intercom_token 应返回 422"""
        payload = {**VALID_UPLOAD_PAYLOAD}
        del payload["intercom_token"]
        resp = client.post("/api/v1/intercom/upload", json=payload)
        assert resp.status_code == 422

    def test_missing_title_returns_422(self, client):
        """缺少 title 应返回 422"""
        payload = {**VALID_UPLOAD_PAYLOAD}
        del payload["title"]
        resp = client.post("/api/v1/intercom/upload", json=payload)
        assert resp.status_code == 422

    def test_missing_body_returns_422(self, client):
        """缺少 body 应返回 422"""
        payload = {**VALID_UPLOAD_PAYLOAD}
        del payload["body"]
        resp = client.post("/api/v1/intercom/upload", json=payload)
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_value_error_returns_422(self, mock_upload, client):
        """业务层 ValueError 应映射为 422"""
        mock_upload.side_effect = ValueError("token 不能为空")
        resp = client.post("/api/v1/intercom/upload", json=VALID_UPLOAD_PAYLOAD)
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.upload_to_intercom")
    def test_api_error_returns_502(self, mock_upload, client):
        """Intercom API 异常应映射为 502"""
        mock_upload.side_effect = Exception("Intercom API error: 403 Forbidden")
        resp = client.post("/api/v1/intercom/upload", json=VALID_UPLOAD_PAYLOAD)
        assert resp.status_code == 502


# ─────────────────────────────────────────────
# GET /api/v1/intercom/collections 端点测试
# ─────────────────────────────────────────────

SAMPLE_COLLECTIONS = [
    {"id": "12345", "name": "Getting Started", "translated_content": {"zh": "快速开始", "en": "Getting Started"}},
    {"id": "67890", "name": "Payments", "translated_content": {"en": "Payments"}},
]


class TestCollectionsEndpoint:
    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_success_returns_200(self, mock_fetch, client):
        """成功响应应返回 200"""
        mock_fetch.return_value = SAMPLE_COLLECTIONS
        resp = client.get("/api/v1/intercom/collections?token=valid-token")
        assert resp.status_code == 200

    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_response_has_collections_key(self, mock_fetch, client):
        """响应应含 collections 和 count 字段"""
        mock_fetch.return_value = SAMPLE_COLLECTIONS
        resp = client.get("/api/v1/intercom/collections?token=valid-token")
        body = resp.json()
        assert "collections" in body
        assert "count" in body
        assert body["count"] == 2

    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_response_items_have_required_fields(self, mock_fetch, client):
        """每个 collection item 应含 id / name / translated_content"""
        mock_fetch.return_value = SAMPLE_COLLECTIONS
        resp = client.get("/api/v1/intercom/collections?token=valid-token")
        item = resp.json()["collections"][0]
        assert "id" in item
        assert "name" in item
        assert "translated_content" in item

    def test_missing_token_returns_422(self, client):
        """缺少 token 应返回 422"""
        resp = client.get("/api/v1/intercom/collections")
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_value_error_returns_422(self, mock_fetch, client):
        """业务层 ValueError 应映射为 422"""
        mock_fetch.side_effect = ValueError("token 不能为空")
        resp = client.get("/api/v1/intercom/collections?token=bad")
        assert resp.status_code == 422

    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_api_error_returns_502(self, mock_fetch, client):
        """Intercom API 异常应映射为 502"""
        mock_fetch.side_effect = Exception("Intercom 401 Unauthorized")
        resp = client.get("/api/v1/intercom/collections?token=bad")
        assert resp.status_code == 502

    @patch("api.routers.intercom_qa.fetch_intercom_collections")
    def test_token_passed_to_core(self, mock_fetch, client):
        """token 参数应传递给核心函数"""
        mock_fetch.return_value = []
        client.get("/api/v1/intercom/collections?token=my-secret-token")
        mock_fetch.assert_called_once_with("my-secret-token")
