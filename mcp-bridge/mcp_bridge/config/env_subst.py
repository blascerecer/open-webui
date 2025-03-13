from string import Template
from typing import Any
import os

from loguru import logger


def substitute_env_vars(config: Any, env: dict[str, str] | None = None) -> Any:
    """Substitute environment variables in a configuration object."""

    # copy the environment if it is not provided
    if env is None:
        env = os.environ.copy()

    assert env is not None, "env is None"  # the guard should have caught this

    # handle strings
    if isinstance(config, str):
        return Template(config).safe_substitute(env)

    # handle other types
    elif isinstance(config, dict):
        return {
            k: substitute_env_vars(v, env) for k, v in config.items() if v is not None
        }

    # handle lists
    elif isinstance(config, list):
        return [substitute_env_vars(v, env) for v in config]

    return config
