from httpx import AsyncClient
from mcp_bridge.config import config

client: AsyncClient = AsyncClient(
    base_url=config.inference_server.base_url,
    headers={"Authorization": f"Bearer {config.inference_server.api_key}", "Content-Type": "application/json"},
    timeout=10000,
)
