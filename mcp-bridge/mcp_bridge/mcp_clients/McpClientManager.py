from typing import Union

from loguru import logger
from mcp import McpError, StdioServerParameters
from mcpx.client.transports.docker import DockerMCPServer

from mcp_bridge.config import config, reload_config
from mcp_bridge.config.final import SSEMCPServer

from .DockerClient import DockerClient
from .SseClient import SseClient
from .StdioClient import StdioClient

client_types = Union[StdioClient, SseClient, DockerClient]


class MCPClientManager:
    clients: dict[str, client_types] = {}

    async def initialize(self):
        """Initialize the MCP Client Manager and start all clients"""

        logger.log("DEBUG", "Initializing MCP Client Manager")

        for server_name, server_config in config.mcp_servers.items():
            self.clients[server_name] = await self.construct_client(
                server_name, server_config
            )

    async def construct_client(self, name, server_config) -> client_types:
        logger.log("DEBUG", f"Constructing client for {server_config}")

        if isinstance(server_config, StdioServerParameters):
            client = StdioClient(name, server_config)
            await client.start()
            return client

        if isinstance(server_config, SSEMCPServer):
            # TODO: implement sse client
            client = SseClient(name, server_config)  # type: ignore
            await client.start()
            return client
        
        if isinstance(server_config, DockerMCPServer):
            client = DockerClient(name, server_config)
            await client.start()
            return client

        raise NotImplementedError("Client Type not supported")

    async def reload_config_and_clients(self):
        """Reload configuration and update clients as needed"""
        logger.info("Reloading configuration and updating clients...")
        
        try:
            # Store old client names
            old_server_names = set(self.clients.keys())
            
            # Reload the configuration
            from mcp_bridge.config import reload_config
            reload_config()
            
            # Get new server names from updated config
            from mcp_bridge.config import config
            new_server_names = set(config.mcp_servers.keys())
            
            logger.info(f"Old servers: {old_server_names}, New servers: {new_server_names}")
            
            # Handle removed servers
            removed_servers = old_server_names - new_server_names
            for server_name in removed_servers:
                logger.info(f"Removing client for removed server: {server_name}")
                client = self.clients.pop(server_name)
                await client.stop()
            
            # For simplicity, let's reinitialize all clients
            # This approach is more robust if client structure varies
            for name in list(self.clients.keys()):
                logger.info(f"Stopping client: {name}")
                client = self.clients[name]
                await client.stop()
                self.clients.pop(name)
            
            # Initialize new clients based on updated config
            logger.info("Initializing clients with updated configuration")
            for server_name, server_config in config.mcp_servers.items():
                logger.info(f"Creating client for server: {server_name}")
                self.clients[server_name] = await self.construct_client(
                    server_name, server_config
                )
            
            logger.info("Configuration and clients reloaded successfully")
            return True
        except Exception as e:
            import traceback
            logger.error(f"Error reloading clients: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def get_client(self, server_name: str):
        return self.clients[server_name]

    def get_clients(self):
        return list(self.clients.items())

    async def get_client_from_tool(self, tool: str):
        for name, client in self.get_clients():
            
            # client cannot have tools if it is not connected
            if not client.session:
                continue

            try:
                list_tools = await client.session.list_tools()
                for client_tool in list_tools.tools:
                    if client_tool.name == tool:
                        return client
            except McpError:
                continue

    async def get_client_from_prompt(self, prompt: str):
        for name, client in self.get_clients():

            # client cannot have prompts if it is not connected
            if not client.session:
                continue

            try:
                list_prompts = await client.session.list_prompts()
                for client_prompt in list_prompts.prompts:
                    if client_prompt.name == prompt:
                        return client
            except McpError:
                continue


ClientManager = MCPClientManager()