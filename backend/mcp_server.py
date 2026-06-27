# backend/mcp_server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# This is a stub for the Wikipedia MCP Server.
# In a real deployment, we would use the official npx @modelcontextprotocol/server-wikipedia
# Here we mock the MCP interface to demonstrate the architecture

server = Server("wikipedia-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_wikipedia",
            description="Query Wikipedia to retrieve factual summaries on a topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for"
                    }
                },
                "required": ["query"]
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_wikipedia":
        query = arguments.get("query")
        # Mocked response
        return [TextContent(type="text", text=f"Factual summary from Wikipedia about {query}...")]
    
    return [TextContent(type="text", text="Tool not found.")]

async def main():
    async with stdio_server() as (read, write):
        init_options = server.create_initialization_options()
        await server.run(read, write, init_options)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
