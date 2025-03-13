from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, Json
from typing import Optional

__all__ = ["initial_settings"]


class InitialSettings(BaseSettings):
    file: Optional[str] = Field("config.json")
    http_url: Optional[str] = Field(None)
    json: Optional[Json] = Field(None)  # allow for raw config to be passed as env var

    load_config: bool = Field(
        True, include_in_schema=False
    )  # this can be used to disable loading the config

    model_config = SettingsConfigDict(
        env_prefix="MCP_BRIDGE__CONFIG__",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


# This will load the InitialSettings from environment variables
initial_settings = InitialSettings()
