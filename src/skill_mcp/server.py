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
from skill_mcp.models_crud import (
    NodeCrudInput,
    QueryGraphInput,
    RelationshipCrudInput,
    SkillCrudInput,
    SkillEnvCrudInput,
    SkillFilesCrudInput,
)
from skill_mcp.tools.node_crud import NodeCrud
from skill_mcp.tools.query_graph import QueryGraph
from skill_mcp.tools.relationship_crud import RelationshipCrud
from skill_mcp.tools.script_tools import ScriptTools
from skill_mcp.tools.skill_crud import SkillCrud
from skill_mcp.tools.skill_env_crud import SkillEnvCrud
from skill_mcp.tools.skill_files_crud import SkillFilesCrud

# Initialize MCP Server
app = Server("skill-mcp")


@app.list_tools()  # type: ignore[misc]
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = []
    tools.extend(SkillCrud.get_tool_definition())
    tools.extend(SkillFilesCrud.get_tool_definition())
    tools.extend(SkillEnvCrud.get_tool_definition())
    tools.extend(ScriptTools.get_script_tools())
    tools.extend(NodeCrud.get_tool_definition())
    tools.extend(RelationshipCrud.get_tool_definition())
    tools.extend(QueryGraph.get_tool_definition())
    return tools


@app.call_tool()  # type: ignore[misc]
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        # Unified CRUD tools
        if name == "skill_crud":
            skill_input = SkillCrudInput(**arguments)
            return await SkillCrud.skill_crud(skill_input)
        elif name == "skill_files_crud":
            files_input = SkillFilesCrudInput(**arguments)
            return await SkillFilesCrud.skill_files_crud(files_input)
        elif name == "skill_env_crud":
            env_input = SkillEnvCrudInput(**arguments)
            return await SkillEnvCrud.skill_env_crud(env_input)

        # Script execution tools
        elif name == "execute_python_code":
            code_input = ExecutePythonCodeInput(**arguments)
            return await ScriptTools.execute_python_code(code_input)
        elif name == "run_skill_script":
            script_input = RunSkillScriptInput(**arguments)
            return await ScriptTools.run_skill_script(script_input)

        # Graph tools
        elif name == "node_crud":
            node_input = NodeCrudInput(**arguments)
            return await NodeCrud.node_crud(node_input)
        elif name == "relationship_crud":
            rel_input = RelationshipCrudInput(**arguments)
            return await RelationshipCrud.relationship_crud(rel_input)
        elif name == "query_graph":
            query_input = QueryGraphInput(**arguments)
            return await QueryGraph.query_graph(query_input)

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
