import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8081"))
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Kubernetes settings
    kubernetes_namespace: str = os.getenv("NAMESPACE", "default")
    mcp_bridge_image: str = os.getenv("MCP_BRIDGE_IMAGE", "ghcr.io/secretiveshell/mcp-bridge/mcp-bridge:0.1.0")
    
    # Security settings
    cors_origins: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()