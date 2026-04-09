"""Tests for api/llm_errors.format_llm_error_detail."""
import pytest

from api.llm_errors import LLM_REGION_NOT_SUPPORTED_KEY, format_llm_error_detail


@pytest.mark.parametrize(
    "exc_text",
    [
        "Error code: 400 - User location is not supported for the API use.",
        "[{'error': {'message': 'User location is not supported for the API use.'}}]",
    ],
)
def test_region_blocked_maps_to_i18n_key(exc_text: str) -> None:
    assert format_llm_error_detail(RuntimeError(exc_text)) == LLM_REGION_NOT_SUPPORTED_KEY


def test_location_api_phrase_maps_to_i18n_key() -> None:
    assert (
        format_llm_error_detail(ValueError("location is not supported for the api use"))
        == LLM_REGION_NOT_SUPPORTED_KEY
    )


def test_other_error_keeps_prefix() -> None:
    detail = format_llm_error_detail(RuntimeError("rate limit"))
    assert detail == "LLM 调用失败: rate limit"
