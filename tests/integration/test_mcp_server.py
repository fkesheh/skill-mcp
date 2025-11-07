"""Integration tests for MCP server with CRUD tools."""

from unittest.mock import patch

import pytest

from skill_mcp.models_crud import (
    SkillCrudInput,
    SkillEnvCrudInput,
    SkillFilesCrudInput,
)
from skill_mcp.tools.skill_crud import SkillCrud
from skill_mcp.tools.skill_env_crud import SkillEnvCrud
from skill_mcp.tools.skill_files_crud import SkillFilesCrud


@pytest.mark.asyncio
async def test_skill_crud_list(sample_skill, temp_skills_dir):
    """Test skill_crud list operation."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        input_data = SkillCrudInput(operation="list")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text


@pytest.mark.asyncio
async def test_skill_crud_get(sample_skill, temp_skills_dir):
    """Test skill_crud get operation."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        input_data = SkillCrudInput(operation="get", skill_name="test-skill")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text
        assert "Files" in text


@pytest.mark.asyncio
async def test_skill_files_crud_read(sample_skill, temp_skills_dir):
    """Test skill_files_crud read operation."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        input_data = SkillFilesCrudInput(
            operation="read", skill_name="test-skill", file_path="SKILL.md"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text


@pytest.mark.asyncio
async def test_skill_files_crud_create_update_delete(sample_skill, temp_skills_dir):
    """Test skill_files_crud create, update, delete flow."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        # Create
        create_input = SkillFilesCrudInput(
            operation="create", skill_name="test-skill", file_path="test.txt", content="initial"
        )
        result = await SkillFilesCrud.skill_files_crud(create_input)
        assert "Successfully created" in result[0].text

        # Read
        read_input = SkillFilesCrudInput(
            operation="read", skill_name="test-skill", file_path="test.txt"
        )
        result = await SkillFilesCrud.skill_files_crud(read_input)
        assert "initial" in result[0].text

        # Update
        update_input = SkillFilesCrudInput(
            operation="update", skill_name="test-skill", file_path="test.txt", content="updated"
        )
        result = await SkillFilesCrud.skill_files_crud(update_input)
        assert "Successfully updated" in result[0].text

        # Read again
        result = await SkillFilesCrud.skill_files_crud(read_input)
        assert "updated" in result[0].text

        # Delete
        delete_input = SkillFilesCrudInput(
            operation="delete", skill_name="test-skill", file_path="test.txt"
        )
        result = await SkillFilesCrud.skill_files_crud(delete_input)
        assert "Successfully deleted" in result[0].text


@pytest.mark.asyncio
async def test_skill_env_crud_read(skill_with_env, temp_skills_dir):
    """Test skill_env_crud read operation."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        input_data = SkillEnvCrudInput(operation="read", skill_name="test-skill")
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) > 0
        text = result[0].text
        assert "API_KEY" in text
        assert "DATABASE_URL" in text


@pytest.mark.asyncio
async def test_skill_env_crud_set(sample_skill, temp_skills_dir):
    """Test skill_env_crud set operation."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        input_data = SkillEnvCrudInput(
            operation="set",
            skill_name="test-skill",
            variables={"NEW_VAR": "value", "ANOTHER": "test"},
        )
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert "Successfully set" in result[0].text

        # Verify it was updated
        read_input = SkillEnvCrudInput(operation="read", skill_name="test-skill")
        read_result = await SkillEnvCrud.skill_env_crud(read_input)
        assert "NEW_VAR" in read_result[0].text


@pytest.mark.asyncio
async def test_server_list_tools():
    """Test MCP server list_tools endpoint returns CRUD tools."""
    from skill_mcp.server import list_tools

    tools = await list_tools()

    assert len(tools) > 0
    tool_names = [t.name for t in tools]

    # Check CRUD tools are present
    assert "skill_crud" in tool_names
    assert "skill_files_crud" in tool_names
    assert "skill_env_crud" in tool_names
    assert "run_skill_script" in tool_names


@pytest.mark.asyncio
async def test_server_skill_crud(sample_skill, temp_skills_dir):
    """Test server call_tool for skill_crud."""
    from skill_mcp.server import call_tool

    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool("skill_crud", {"operation": "list"})

        assert len(result) > 0
        assert "test-skill" in result[0].text


@pytest.mark.asyncio
async def test_server_skill_files_crud(sample_skill, temp_skills_dir):
    """Test server call_tool for skill_files_crud."""
    from skill_mcp.server import call_tool

    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool(
            "skill_files_crud",
            {"operation": "read", "skill_name": "test-skill", "file_path": "SKILL.md"},
        )

        assert len(result) > 0
        assert "test-skill" in result[0].text


@pytest.mark.asyncio
async def test_server_skill_env_crud(skill_with_env, temp_skills_dir):
    """Test server call_tool for skill_env_crud."""
    from skill_mcp.server import call_tool

    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool(
            "skill_env_crud", {"operation": "read", "skill_name": "test-skill"}
        )

        assert len(result) > 0
        assert "API_KEY" in result[0].text


@pytest.mark.asyncio
async def test_server_unknown_tool():
    """Test server call_tool with unknown tool."""
    from skill_mcp.server import call_tool

    result = await call_tool("unknown_tool", {})

    assert "Unknown tool" in result[0].text
