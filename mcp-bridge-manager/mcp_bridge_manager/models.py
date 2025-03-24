from pydantic import BaseModel
from typing import Dict, List, Optional

class InferenceServer(BaseModel):
    baseUrl: str
    apiKey: str

class McpServer(BaseModel):
    command: str
    args: List[str] = []
    apiKey: Optional[str] = None
    credentials: Optional[Dict] = None

class BridgeCreateRequest(BaseModel):
    userId: str
    inferenceServer: InferenceServer
    mcpServers: Dict[str, McpServer] = {}

class BridgeInfo(BaseModel):
    status: str
    endpoint: str
    availableServers: List[str]

class KeyRequest(BaseModel):
    server: str
    command: str
    args: List[str] = []
    apiKey: str