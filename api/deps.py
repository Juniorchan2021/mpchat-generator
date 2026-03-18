import os

from fastapi import Header, HTTPException

# Re-enable by setting MPCHAT_AUTH_ENABLED=true AND MPCHAT_API_KEY on the server
_AUTH_ENABLED = os.getenv("MPCHAT_AUTH_ENABLED", "").lower() == "true"
EXPECTED_KEY = os.getenv("MPCHAT_API_KEY", "") if _AUTH_ENABLED else ""


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not EXPECTED_KEY:
        return
    if x_api_key != EXPECTED_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
