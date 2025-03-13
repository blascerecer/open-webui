from mcp import types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl
from mcp_bridge.mcp_clients.McpClientManager import ClientManager
from loguru import logger

__all__ = ["server", "options"]

server = Server("MCP-Bridge")

## list functions


@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    prompts = []
    for name, client in ClientManager.get_clients():
        # if client is None, then we cannot list the prompts
        if client is None:
            logger.error(f"Client '{name}' not found")
            continue

        client_prompts = await client.list_prompts()
        prompts.extend(client_prompts.prompts)
    return prompts


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    resources = []
    for name, client in ClientManager.get_clients():
        try:
            client_resources = await client.list_resources()
            resources.extend(client_resources.resources)
        except Exception as e:
            logger.error(f"Error listing resources for {name}: {e}")
    return resources


@server.list_resource_templates()
async def list_resource_templates() -> list[types.ResourceTemplate]:
    return []


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    tools = []
    for name, client in ClientManager.get_clients():
        # if client is None, then we cannot list the tools
        if client is None:
            logger.error(f"Client '{name}' not found")
            continue

        client_tools = await client.list_tools()
        tools.extend(client_tools.tools)
    return tools


## get functions


@server.get_prompt()
async def get_prompt(name: str, args: dict[str, str] | None) -> types.GetPromptResult:
    client = await ClientManager.get_client_from_prompt(name)

    # if client is None, then we cannot get the prompt
    if client is None:
        raise Exception(f"Prompt '{name}' not found")

    # if args is None, then we should use an empty dict
    if args is None:
        args = {}

    result = await client.get_prompt(name, args)
    if result is None:
        raise Exception(f"Prompt '{name}' not found")

    return result


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str | bytes:
    for name, client in ClientManager.get_clients():
        try:
            client_resources = await client.list_resources()
            if str(uri) in map(lambda x: str(x.uri), client_resources.resources):
                response = await client.read_resource(uri)
                for resource in response:
                    if resource.mimeType == "text/plain":
                        assert isinstance(resource, types.TextResourceContents)
                        assert type(resource.text) is str
                        return resource.text

                    elif resource.mimeType == "application/octet-stream":
                        assert isinstance(resource, types.BlobResourceContents)
                        assert type(resource.blob) is bytes
                        return resource.blob

                    else:
                        raise Exception(
                            f"Unsupported resource type: {resource.mimeType}"
                        )

        except Exception as e:
            logger.error(f"Error listing resources for {name}: {e}")

    raise Exception(f"Resource '{uri}' not found")


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    client = await ClientManager.get_client_from_tool(name)

    # if client is None, then we cannot call the tool
    if client is None:
        raise Exception(f"Tool '{name}' not found")

    # if arguments is None, then we should use an empty dict
    if arguments is None:
        arguments = {}

    return (await client.call_tool(name, arguments)).content


# options

options = InitializationOptions(
    server_name="MCP-Bridge",
    server_version="0.2.0",
    capabilities=server.get_capabilities(
        notification_options=NotificationOptions(),
        experimental_capabilities={},
    ),
)
