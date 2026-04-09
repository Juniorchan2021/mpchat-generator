"""Map upstream LLM exceptions to stable API detail strings (i18n keys where applicable)."""

LLM_REGION_NOT_SUPPORTED_KEY = "err.llmRegionNotSupported"


def format_llm_error_detail(exc: BaseException) -> str:
    """Return a client-displayable detail: i18n key for known cases, else prefixed raw message."""
    msg = str(exc).lower()
    if "user location is not supported" in msg:
        return LLM_REGION_NOT_SUPPORTED_KEY
    if "location is not supported for the api" in msg:
        return LLM_REGION_NOT_SUPPORTED_KEY
    return f"LLM 调用失败: {exc}"
