import json
import httpx
from typing import Any
from loguru import logger


def load_config(url: str) -> dict[str, Any]:
    try:
        resp = httpx.get(str(url))
        return resp.json()

    except httpx.ConnectError:
        logger.error(f"could not connect to {httpx.URL(url).host}")

    except json.JSONDecodeError:
        logger.error(f"failed to parse json from {httpx.URL(url)}")

    return {}
