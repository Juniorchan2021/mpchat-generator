"""Tests for api/routers/ideation.py (TestClient + mock, no real LLM)."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.llm_errors import LLM_REGION_NOT_SUPPORTED_KEY


@pytest.fixture
def client() -> TestClient:
    from api.main import app

    return TestClient(app)


IDEATION_PAYLOAD = {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "api_key": "test-key",
    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "core_keyword": "crypto",
    "industry": "web3",
    "count": 5,
    "language": "auto",
}


class TestIdeationTopicsEndpoint:
    @patch("api.routers.ideation.generate_topics")
    def test_success_returns_200(self, mock_gen, client: TestClient) -> None:
        mock_gen.return_value = [
            {
                "title": "Test",
                "search_intent": "informational",
                "difficulty": "easy",
                "keywords": ["crypto"],
            }
        ]
        resp = client.post("/api/v1/ideation/topics", json=IDEATION_PAYLOAD)
        assert resp.status_code == 200
        body = resp.json()
        assert body["core_keyword"] == "crypto"
        assert len(body["topics"]) == 1

    @patch("api.routers.ideation.generate_topics")
    def test_gemini_region_error_returns_i18n_key_detail(self, mock_gen, client: TestClient) -> None:
        mock_gen.side_effect = RuntimeError(
            "Error code: 400 - [{'error': {'message': 'User location is not supported for the API use.'}}]"
        )
        resp = client.post("/api/v1/ideation/topics", json=IDEATION_PAYLOAD)
        assert resp.status_code == 502
        assert resp.json()["detail"] == LLM_REGION_NOT_SUPPORTED_KEY

    @patch("api.routers.ideation.generate_topics")
    def test_other_llm_error_returns_prefixed_message(self, mock_gen, client: TestClient) -> None:
        mock_gen.side_effect = RuntimeError("connection reset")
        resp = client.post("/api/v1/ideation/topics", json=IDEATION_PAYLOAD)
        assert resp.status_code == 502
        assert resp.json()["detail"] == "LLM 调用失败: connection reset"
