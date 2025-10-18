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

from skill_mcp.models import (
    ListSkillsInput,
    GetSkillDetailsInput,
    ReadSkillFileInput,
    CreateSkillFileInput,
    UpdateSkillFileInput,
    DeleteSkillFileInput,
    RunSkillScriptInput,
    ReadSkillEnvInput,
    UpdateSkillEnvInput,
)
from skill_mcp.tools.skill_tools import SkillTools
from skill_mcp.tools.file_tools import FileTools
from skill_mcp.tools.script_tools import ScriptTools


# Initialize MCP Server
app = Server("skill-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    tools = []
    tools.extend(SkillTools.get_list_tools())
    tools.extend(FileTools.get_file_tools())
    tools.extend(ScriptTools.get_script_tools())
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    try:
        # Skill tools
        if name == "list_skills":
            return await SkillTools.list_skills()
        elif name == "get_skill_details":
            input_data = GetSkillDetailsInput(**arguments)
            return await SkillTools.get_skill_details(input_data)
        
        # File tools
        elif name == "read_skill_file":
            input_data = ReadSkillFileInput(**arguments)
            return await FileTools.read_skill_file(input_data)
        elif name == "create_skill_file":
            input_data = CreateSkillFileInput(**arguments)
            return await FileTools.create_skill_file(input_data)
        elif name == "update_skill_file":
            input_data = UpdateSkillFileInput(**arguments)
            return await FileTools.update_skill_file(input_data)
        elif name == "delete_skill_file":
            input_data = DeleteSkillFileInput(**arguments)
            return await FileTools.delete_skill_file(input_data)
        
        # Script tools
        elif name == "run_skill_script":
            input_data = RunSkillScriptInput(**arguments)
            return await ScriptTools.run_skill_script(input_data)
        elif name == "read_skill_env":
            input_data = ReadSkillEnvInput(**arguments)
            return await ScriptTools.read_skill_env(input_data)
        elif name == "update_skill_env":
            input_data = UpdateSkillEnvInput(**arguments)
            return await ScriptTools.update_skill_env(input_data)
        
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
