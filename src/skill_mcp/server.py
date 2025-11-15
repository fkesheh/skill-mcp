#!/usr/bin/env python3
"""
Skill Management MCP Server

A Model Context Protocol server for managing Claude skills with per-skill environment variables
and automatic dependency management for Python scripts.
"""

from typing import Any

import mcp.server.stdio
from mcp import types
from mcp.server import Server

from skill_mcp.models import ExecutePythonCodeInput, RunSkillScriptInput
from skill_mcp.tools.env_file_crud import EnvFileCrud
from skill_mcp.tools.node_crud import NodeCrud
from skill_mcp.tools.query_graph import QueryGraph
from skill_mcp.tools.relationship_crud import RelationshipCrud
from skill_mcp.tools.script_tools import ScriptTools

# Initialize MCP Server
app = Server("skill-mcp")


@app.list_tools()  # type: ignore[misc]
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = []
    # Graph tools (new node-based architecture)
    tools.extend(NodeCrud.get_tool_definition())
    tools.extend(RelationshipCrud.get_tool_definition())
    tools.extend(QueryGraph.get_tool_definition())
    tools.extend(EnvFileCrud.get_tool_definition())
    # Script execution tools
    tools.extend(ScriptTools.get_script_tools())
    return tools


@app.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        # Graph tools (new node-based architecture)
        if name == "node_crud":
            return await NodeCrud.node_crud(arguments)
        elif name == "relationship_crud":
            return await RelationshipCrud.relationship_crud(arguments)
        elif name == "query_graph":
            return await QueryGraph.query_graph(arguments)
        elif name == "env_file_crud":
            return await EnvFileCrud.env_file_crud(arguments)

        # Script execution tools
        elif name == "execute_python_code":
            code_input = ExecutePythonCodeInput(**arguments)
            return await ScriptTools.execute_python_code(code_input)
        elif name == "run_skill_script":
            script_input = RunSkillScriptInput(**arguments)
            return await ScriptTools.run_skill_script(script_input)

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main() -> None:
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run() -> None:
    """Entry point for the MCP server."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
