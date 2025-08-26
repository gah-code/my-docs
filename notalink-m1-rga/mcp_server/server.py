from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .tools import notes as notes_tools
from .tools import ai as ai_tools

def create_mcp() -> FastMCP:
    mcp = FastMCP("notalink")
    notes_tools.register_tools(mcp)
    ai_tools.register_tools(mcp)
    return mcp

def main() -> None:
    create_mcp().run(transport="stdio")

if __name__ == "__main__":
    main()
