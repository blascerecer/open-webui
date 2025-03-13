from contextlib import asynccontextmanager
from mcp_bridge.mcp_clients.McpClientManager import ClientManager
from loguru import logger


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for fastapi"""

    # startup
    logger.log("DEBUG", "Entered fastapi lifespan")
    await ClientManager.initialize()
    logger.log("DEBUG", "Initialized MCP Client Manager")

    logger.log("DEBUG", "Yielding lifespan")
    yield
    logger.log("DEBUG", "Returned form lifespan yield")

    # shutdown

    logger.log("DEBUG", "Exiting fastapi lifespan")
