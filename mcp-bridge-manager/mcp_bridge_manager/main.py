from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json

from mcp_bridge_manager.models import (
    BridgeCreateRequest,
    BridgeInfo,
    KeyRequest
)
from mcp_bridge_manager.kubernetes import (
    create_config_map,
    create_secrets,
    create_deployment,
    create_service,
    delete_bridge,
    get_bridge_status
)
from mcp_bridge_manager.config import settings

app = FastAPI(
    title="MCP Bridge Manager",
    description="Service for managing user-specific MCP Bridge instances",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Endpoints -----

@app.post("/api/bridge/create", response_model=BridgeInfo)
async def create_bridge(request: BridgeCreateRequest):
    """Create or update an MCP Bridge for a user."""
    user_id = request.userId
    
    # Create ConfigMap with configurations
    create_config_map(user_id, request.inferenceServer, request.mcpServers)
    
    # Create Secrets for API keys
    create_secrets(user_id, request.inferenceServer, request.mcpServers)
    
    # Create Deployment
    create_deployment(user_id)
    
    # Create Service
    create_service(user_id)
    
    # Return connection info
    return get_bridge_status(user_id)

@app.get("/api/bridge/{user_id}", response_model=BridgeInfo)
async def get_bridge(user_id: str):
    """Get information about a user's MCP Bridge."""
    return get_bridge_status(user_id)

@app.delete("/api/bridge/{user_id}")
async def remove_bridge(user_id: str):
    """Remove a user's MCP Bridge."""
    delete_bridge(user_id)
    return {"message": "Bridge deleted successfully"}

@app.put("/api/keys/{user_id}")
async def store_key(user_id: str, request: KeyRequest):
    """Store a new API key for a user."""
    from mcp_bridge_manager.kubernetes import store_api_key
    return store_api_key(user_id, request)

@app.get("/api/keys/{user_id}")
async def list_keys(user_id: str):
    """List available MCP Servers for a user."""
    from mcp_bridge_manager.kubernetes import list_api_keys
    return list_api_keys(user_id)

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/readyz")
async def readiness_check():
    """Readiness check endpoint."""
    # Check if we can connect to the Kubernetes API
    try:
        status = get_bridge_status("test-readiness")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_bridge_manager.main:app", 
        host=settings.host, 
        port=settings.port,
        reload=settings.debug
    )