from pydantic import BaseModel, Field


class McpServerStatus(BaseModel):
    name: str = Field(..., description="Name of the MCP server")
    online: bool = Field(..., description="Whether the server is online")
    enabled: bool = Field(True, description="Whether the server is enabled")
