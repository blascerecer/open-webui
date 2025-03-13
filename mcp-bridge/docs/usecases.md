# Usecase Examples

This document contains a list of usecases for the MCP-Bridge. These usecases are not exhaustive, but they should give you an idea of what the application can do.

## Usecase 1: OpenwebUI with MCP-Bridge

This is documented in the readme. You can point OpenWebUI at the openAI compatible endpoint and it will work with MCP tools.

## Usecase 2: Custom Programs with MCP-Bridge Rest API

You can use the MCP-Bridge Rest API to call MCP tools from your own program. This allows you to offload any complexity of MCP servers to the MCP-Bridge, which can be used to test your configuration.

## Usecase 3: Custom Programs with MCP-Bridge SSE server

You can use the MCP-Bridge SSE server to call MCP tools from your own program. This allows you to offload configuration and session management to the MCP-Bridge, and means you only need to support a single MCP server. No need to map tools to servers.

## Usecase 4: Docker to SSE adapter

You can use docker in docker with MCP-Bridge to spawn many isolated servers and the connect to them all over SSE. This allows for larger scale homelab style deployments.

## Usecase 5: Sampling Middleware

Unfortunately most clients do not support [sampling](https://modelcontextprotocol.info/docs/concepts/sampling/). MCP-Bridge can be used as a sampling middleware to help resolve this. By using a SSE connector like [lightconetech/mcp-gateway](https://github.com/lightconetech/mcp-gateway) you can add sampling support to more limited STDIO clients like claude desktop that don't support it natively.
