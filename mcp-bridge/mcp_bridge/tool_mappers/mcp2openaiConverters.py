from mcp import Tool
from lmos_openai_types import ChatCompletionTool


def mcp2openai(mcp_tool: Tool) -> ChatCompletionTool:
    """Convert a MCP Tool to an OpenAI ChatCompletionTool."""

    return ChatCompletionTool(
        type="function",
        function={
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema,
            "strict": False,
        },
    )
