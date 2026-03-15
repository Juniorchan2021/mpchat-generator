import os

from fastapi import Header, HTTPException


EXPECTED_KEY = os.getenv("MPCHAT_API_KEY")


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if EXPECTED_KEY and x_api_key != EXPECTED_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
