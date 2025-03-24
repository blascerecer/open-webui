# Integrating MCP Bridge Manager with Open WebUI

This guide explains how to integrate the MCP Bridge Manager with your Open WebUI application to dynamically create and destroy MCP Bridge instances for users.

## Overview

When a user logs in to Open WebUI, you'll need to:
1. Request a new MCP Bridge instance from the Manager
2. Connect to the user's bridge
3. Clean up when the user logs out

## Integration Steps

### 1. Add Environment Variables

Ensure your Open WebUI deployment includes the environment variable:

```yaml
env:
- name: MCP_BRIDGE_MANAGER_URL
  value: "http://mcp-bridge-manager-service:8081"
```

### 2. Add Code to Handle Login Events

When a user successfully logs in, add code to create their MCP Bridge:

```javascript
// Example for JavaScript frontend
async function setupUserMcpBridge(userId) {
  try {
    // Get existing API keys from local storage or another source
    const savedKeys = getSavedApiKeys(userId);
    
    // Create request payload
    const payload = {
      userId: userId,
      inferenceServer: {
        baseUrl: "https://your-inference-server.com",
        apiKey: savedKeys.inferenceServerKey || ""
      },
      mcpServers: savedKeys.mcpServers || {}
    };
    
    // Request bridge creation
    const response = await fetch(`${MCP_BRIDGE_MANAGER_URL}/api/bridge/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create MCP Bridge: ${response.statusText}`);
    }
    
    const bridgeInfo = await response.json();
    
    // Store bridge endpoint for future requests
    sessionStorage.setItem('mcpBridgeEndpoint', bridgeInfo.endpoint);
    
    // If no servers configured, prompt the user
    if (bridgeInfo.availableServers.length === 0) {
      showApiKeyConfigUI();
    }
    
    return bridgeInfo;
  } catch (error) {
    console.error("Error setting up MCP Bridge:", error);
    // Show error to user
  }
}
```

### 3. Add Code to Handle Logout Events

When a user logs out, add code to destroy their MCP Bridge:

```javascript
async function cleanupUserMcpBridge(userId) {
  try {
    const response = await fetch(`${MCP_BRIDGE_MANAGER_URL}/api/bridge/${userId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      console.warn(`Warning: Failed to clean up MCP Bridge: ${response.statusText}`);
    }
    
    // Clear bridge endpoint
    sessionStorage.removeItem('mcpBridgeEndpoint');
  } catch (error) {
    console.error("Error cleaning up MCP Bridge:", error);
  }
}
```

### 4. Add API Key Management UI

Create a UI for users to add or update their API keys:

```javascript
async function saveApiKey(userId, serverName, serverConfig) {
  try {
    const response = await fetch(`${MCP_BRIDGE_MANAGER_URL}/api/keys/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        server: serverName,
        command: serverConfig.command,
        args: serverConfig.args,
        apiKey: serverConfig.apiKey
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to save API key: ${response.statusText}`);
    }
    
    // Update local storage
    const savedKeys = getSavedApiKeys(userId);
    savedKeys.mcpServers = savedKeys.mcpServers || {};
    savedKeys.mcpServers[serverName] = {
      command: serverConfig.command,
      args: serverConfig.args,
      apiKey: serverConfig.apiKey
    };
    setSavedApiKeys(userId, savedKeys);
    
    return await response.json();
  } catch (error) {
    console.error("Error saving API key:", error);
    // Show error to user
  }
}
```

### 5. Add MCP Bridge Service Proxy

Modify your API calls to route through the user's MCP Bridge:

```javascript
async function callServiceWithMcp(endpoint, method, body) {
  const mcpBridgeEndpoint = sessionStorage.getItem('mcpBridgeEndpoint');
  
  if (!mcpBridgeEndpoint) {
    throw new Error("No MCP Bridge endpoint available");
  }
  
  // Format depends on your MCP Bridge implementation
  const url = `http://${mcpBridgeEndpoint}/v1/${endpoint}`;
  
  const response = await fetch(url, {
    method: method,
    headers: {
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  
  return await response.json();
}
```

### 6. Auto-Reconnect Logic

Add logic to reconnect to a user's bridge if the page is refreshed:

```javascript
async function reconnectToMcpBridge(userId) {
  try {
    const response = await fetch(`${MCP_BRIDGE_MANAGER_URL}/api/bridge/${userId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to get MCP Bridge status: ${response.statusText}`);
    }
    
    const bridgeInfo = await response.json();
    
    if (bridgeInfo.status === "running") {
      // Reconnect to existing bridge
      sessionStorage.setItem('mcpBridgeEndpoint', bridgeInfo.endpoint);
      return bridgeInfo;
    } else if (bridgeInfo.status === "not_found") {
      // Need to create a new bridge
      return await setupUserMcpBridge(userId);
    } else {
      // Bridge is starting, wait and try again
      await new Promise(resolve => setTimeout(resolve, 2000));
      return await reconnectToMcpBridge(userId);
    }
  } catch (error) {
    console.error("Error reconnecting to MCP Bridge:", error);
    // Show error to user
  }
}
```

## Backend Integration (Python)

If you're using Python for your Open WebUI backend, you can use code like this:

```python
import httpx
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()
MCP_BRIDGE_MANAGER_URL = "http://mcp-bridge-manager-service:8081"

class McpBridgeRequest(BaseModel):
    userId: str
    inferenceServer: dict
    mcpServers: dict = {}

@router.post("/api/auth/login")
async def login(login_data: dict):
    # Your existing login logic
    # ...
    
    # After successful login, create MCP Bridge
    user_id = authenticated_user.id
    
    try:
        # Get saved keys for this user
        saved_keys = get_user_saved_keys(user_id)
        
        # Create MCP Bridge for this user
        bridge_request = McpBridgeRequest(
            userId=user_id,
            inferenceServer={
                "baseUrl": "https://inference.example.com",
                "apiKey": saved_keys.get("inferenceServerKey", "")
            },
            mcpServers=saved_keys.get("mcpServers", {})
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_BRIDGE_MANAGER_URL}/api/bridge/create",
                json=bridge_request.dict()
            )
            
            if response.status_code != 200:
                # Log error but don't fail login
                print(f"Failed to create MCP Bridge: {response.text}")
            else:
                bridge_info = response.json()
        
        # Return bridge info with login response
        return {
            "user": authenticated_user,
            "token": auth_token,
            "mcpBridge": bridge_info
        }
    except Exception as e:
        # Log error but don't fail login
        print(f"Error setting up MCP Bridge: {str(e)}")
        return {
            "user": authenticated_user,
            "token": auth_token
        }

@router.post("/api/auth/logout")
async def logout(user_id: str):
    # Your existing logout logic
    # ...
    
    # Delete the user's MCP Bridge
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{MCP_BRIDGE_MANAGER_URL}/api/bridge/{user_id}"
            )
    except Exception as e:
        # Log error but don't fail logout
        print(f"Error deleting MCP Bridge: {str(e)}")
    
    return {"message": "Logged out successfully"}
```

## UI Components

Create these UI components in your frontend:

1. **API Key Management Page**: Allow users to add/edit API keys for different services
2. **Connection Status Indicator**: Show if the MCP Bridge is connected
3. **Error Handling**: Display meaningful error messages if bridge operations fail

## Security Considerations

1. **Authentication**: Add proper authentication to the MCP Bridge Manager API
2. **Secure Storage**: Don't store API keys in browser localStorage/sessionStorage
3. **HTTPS**: Ensure all communication uses HTTPS in production
4. **Timeouts**: Implement session timeouts to clean up idle bridges
5. **Logging**: Add audit logging for security-sensitive operations

## Testing the Integration

1. Deploy the MCP Bridge Manager
2. Implement the integration code
3. Test the full user flow:
   - User logs in → Bridge is created
   - User configures API keys → Keys are stored securely
   - User uses services → Requests go through their bridge
   - User logs out → Bridge is destroyed
   - User logs back in → Bridge is recreated with saved keys