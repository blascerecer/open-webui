import subprocess
import json
import os
from typing import Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mcp_bridge.mcp_clients.McpClientManager import ClientManager
from mcp.types import ListToolsResult, CallToolResult
from loguru import logger
from typing import Dict, List, Any, Optional

router = APIRouter(prefix="/tools")


@router.get("")
async def get_tools() -> dict[str, ListToolsResult]:
    """Get all tools from all MCP clients"""

    tools = {}

    for name, client in ClientManager.get_clients():
        tools[name] = await client.list_tools()

    return tools


@router.post("/{tool_name}/call")
async def call_tool(tool_name: str, arguments: dict[str, Any] = {}) -> CallToolResult:
    """Call a tool"""

    client = await ClientManager.get_client_from_tool(tool_name)
    if not client:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return await client.call_tool(tool_name, arguments)


class UpdateMCPServersRequest(BaseModel):
    """
    Request model for updating MCP servers
    
    Attributes:
        serversToRemove (List[str]): List of server IDs to remove
        serversToAdd (List[str]): List of server IDs to add
        serverConfigs (Dict[str, Dict[str, Any]]): Dictionary of server configurations
            where the key is the server ID and the value is the server configuration
    """
    serversToRemove: List[str] = []
    serversToAdd: List[str] = []
    serverConfigs: Dict[str, Dict[str, Any]] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "serversToRemove": ["server-to-remove"],
                "serversToAdd": ["flux-mcp-server", "@smithery-ai-brave-search"],
                "serverConfigs": {
                    "flux-mcp-server": {
                        "command": "/path/to/server/index.js",
                        "env": {
                            "API_TOKEN": "your-token"
                        }
                    },
                    "@smithery-ai-brave-search": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@smithery/cli@latest",
                            "run",
                            "@smithery-ai/brave-search",
                            "--config",
                            "\"{\\\"apiKey\\\":\\\"your-api-key\\\"}\""
                        ]
                    }
                }
            }
        }

def install_mcp_server(server_id: str, server_config: Dict[str, Any]) -> bool:
    """
    Install an MCP server using npx command before adding it to the configuration
    
    Args:
        server_id: The ID of the server to install
        server_config: The configuration for the server
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Only attempt installation for servers that use npx with @smithery/cli
        if (server_config.get("command") == "npx" and 
            len(server_config.get("args", [])) >= 3 and
            "@smithery/cli" in server_config["args"][1]):
            
            # Extract the package name from the args
            package_name = None
            for i, arg in enumerate(server_config["args"]):
                if arg == "run" and i + 1 < len(server_config["args"]):
                    package_name = server_config["args"][i + 1]
                    break
            
            if not package_name:
                logger.warning(f"Could not determine package name for server {server_id}")
                return False
            
            # Create an answers file for non-interactive installation
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                # Write yes to the first question about sharing data
                f.write("Yes\n")
                # Write empty strings for required credentials
                # For Spotify integration, provide empty strings for the client ID and secret
                f.write("\n\n")  # Two newlines for two empty inputs
                answers_file = f.name
            
            try:
                # Construct the installation command with input from the answers file
                install_cmd = ["npx", "-y", "@smithery/cli@latest", "install", package_name, "--client", "claude"]
                
                logger.info(f"Installing MCP server {server_id} with command: {' '.join(install_cmd)}")
                
                # Run the installation command with input from the answers file
                with open(answers_file, 'r') as answers:
                    process = subprocess.run(
                        install_cmd,
                        stdin=answers,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                
                logger.debug(f"Installation stdout: {process.stdout}")
                logger.debug(f"Installation stderr: {process.stderr}")
                
                if process.returncode != 0:
                    logger.error(f"Error installing MCP server {server_id}, process returned code {process.returncode}")
                    logger.error(f"Installation output: {process.stdout}\n{process.stderr}")
                    return False
                    
                logger.info(f"Successfully installed MCP server {server_id}")
                return True
            finally:
                # Clean up the answers file
                try:
                    os.unlink(answers_file)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary answers file: {e}")
        else:
            # If not a smithery package or doesn't need installation, consider it successful
            logger.info(f"Server {server_id} doesn't require installation")
            return True
            
    except Exception as e:
        logger.error(f"Exception during installation of MCP server {server_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@router.post("/servers/update", status_code=200)
async def update_mcp_servers(request: UpdateMCPServersRequest) -> dict:
    """Update MCP servers by installing, adding and removing specified servers"""
    try:
        # Path to the config file
        config_path = 'mcp_config.json'
        
        logger.info(f"Opening config file at: {config_path}")
        
        # Create the file with default structure if it doesn't exist
        if not os.path.exists(config_path):
            logger.info(f"Config file {config_path} does not exist, creating it")
            default_config = {
                "mcpServers": {}
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        # Read the current configuration
        with open(config_path, 'r') as f:
            config_content = f.read()
            logger.debug(f"Config content: {config_content[:100]}...")  # Log first 100 chars
            config = json.loads(config_content)
        
        # Ensure the mcpServers key exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
            
        # Keep track of changes made
        changes = {
            "added": [],
            "removed": [],
            "updated": [],
            "installation_failed": []
        }
        
        # Remove servers if they exist in the config
        for server_id in request.serversToRemove:
            if server_id in config["mcpServers"]:
                del config["mcpServers"][server_id]
                changes["removed"].append(server_id)
                logger.info(f"Removed server: {server_id}")
        
        # Add or update servers
        for server_id in request.serversToAdd:
            server_config = request.serverConfigs.get(server_id)
            if server_config:
                logger.info(f"Processing server {server_id} with config: {server_config}")
                
                # Skip installation and just add to configuration
                if server_id not in config["mcpServers"]:
                    config["mcpServers"][server_id] = server_config
                    changes["added"].append(server_id)
                    logger.info(f"Added server: {server_id} with configuration from request")
                else:
                    config["mcpServers"][server_id] = server_config
                    changes["updated"].append(server_id)
                    logger.info(f"Updated server: {server_id} with configuration from request")
            
        # Log the updated config
        logger.info(f"Updated config2: {json.dumps(config, indent=2)}")
        
        # Write the updated configuration back to the file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Attempt to reload clients with new configuration
        reload_success = False
        try:
            logger.info("Attempting to reload MCP clients...")
            reload_success = await ClientManager.reload_config_and_clients()
            logger.info(f"Client reload completed with result: {reload_success}")
        except Exception as reload_error:
            logger.error(f"Error during client reload: {str(reload_error)}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info('MCP server configuration updated successfully')
        return {
            "success": True,
            "reload_success": reload_success,
            "message": "MCP server configuration updated successfully",
            "changes": changes
        }
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise HTTPException(
            status_code=500, 
            detail=f"Configuration file not found: {config_path}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Invalid JSON in configuration file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating MCP server configuration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Error updating MCP server configuration: {str(e)}"
        )