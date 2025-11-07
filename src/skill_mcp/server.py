#!/usr/bin/env python3
"""
Skill Management MCP Server

A Model Context Protocol server for managing Claude skills with per-skill environment variables
and automatic dependency management for Python scripts.
"""

from typing import Any
from mcp.server import Server
from mcp import types
import mcp.server.stdio

from skill_mcp.models import RunSkillScriptInput
from skill_mcp.models_crud import (
    SkillCrudInput,
    SkillFilesCrudInput,
    SkillEnvCrudInput,
)
from skill_mcp.tools.skill_crud import SkillCrud
from skill_mcp.tools.skill_files_crud import SkillFilesCrud
from skill_mcp.tools.skill_env_crud import SkillEnvCrud
from skill_mcp.tools.script_tools import ScriptTools


# Initialize MCP Server
app = Server("skill-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = []
    tools.extend(SkillCrud.get_tool_definition())
    tools.extend(SkillFilesCrud.get_tool_definition())
    tools.extend(SkillEnvCrud.get_tool_definition())
    tools.extend(ScriptTools.get_script_tools())
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        # Unified CRUD tools
        if name == "skill_crud":
            input_data = SkillCrudInput(**arguments)
            return await SkillCrud.skill_crud(input_data)
        elif name == "skill_files_crud":
            input_data = SkillFilesCrudInput(**arguments)
            return await SkillFilesCrud.skill_files_crud(input_data)
        elif name == "skill_env_crud":
            input_data = SkillEnvCrudInput(**arguments)
            return await SkillEnvCrud.skill_env_crud(input_data)

        # Script execution tool (unchanged)
        elif name == "run_skill_script":
            input_data = RunSkillScriptInput(**arguments)
            return await ScriptTools.run_skill_script(input_data)

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
