import json
from typing import Any
from loguru import logger


def load_config(file: str) -> dict[str, Any]:
    try:
        with open(file, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        logger.warning(f'the "{file}" file was not found')

    except Exception:
        logger.error(f'there was an error reading the "{file}" file')

    return {}
