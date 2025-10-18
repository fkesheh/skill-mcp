"""Integration tests for MCP server."""

import pytest
from unittest.mock import patch
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


@pytest.mark.asyncio
async def test_list_skills_tool(sample_skill, temp_skills_dir):
    """Test list_skills tool."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        result = await SkillTools.list_skills()
        
        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text


@pytest.mark.asyncio
async def test_get_skill_details_tool(sample_skill, temp_skills_dir):
    """Test get_skill_details tool."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        input_data = GetSkillDetailsInput(skill_name="test-skill")
        result = await SkillTools.get_skill_details(input_data)
        
        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text
        assert "scripts" in text.lower()


@pytest.mark.asyncio
async def test_read_file_tool(sample_skill, temp_skills_dir):
    """Test read_skill_file tool."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        input_data = ReadSkillFileInput(skill_name="test-skill", file_path="SKILL.md")
        result = await FileTools.read_skill_file(input_data)
        
        assert len(result) > 0
        text = result[0].text
        assert "test-skill" in text


@pytest.mark.asyncio
async def test_create_update_delete_file_flow(sample_skill, temp_skills_dir):
    """Test create, update, delete file flow."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        # Create
        create_input = CreateSkillFileInput(
            skill_name="test-skill",
            file_path="test.txt",
            content="initial"
        )
        result = await FileTools.create_skill_file(create_input)
        assert "Successfully created" in result[0].text
        
        # Read
        read_input = ReadSkillFileInput(skill_name="test-skill", file_path="test.txt")
        result = await FileTools.read_skill_file(read_input)
        assert "initial" in result[0].text
        
        # Update
        update_input = UpdateSkillFileInput(
            skill_name="test-skill",
            file_path="test.txt",
            content="updated"
        )
        result = await FileTools.update_skill_file(update_input)
        assert "Successfully updated" in result[0].text
        
        # Read again
        result = await FileTools.read_skill_file(read_input)
        assert "updated" in result[0].text
        
        # Delete
        delete_input = DeleteSkillFileInput(
            skill_name="test-skill",
            file_path="test.txt"
        )
        result = await FileTools.delete_skill_file(delete_input)
        assert "Successfully deleted" in result[0].text


@pytest.mark.asyncio
async def test_read_nonexistent_file(temp_skills_dir):
    """Test reading a nonexistent file."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        read_input = ReadSkillFileInput(skill_name="test-skill", file_path="nonexistent.txt")
        result = await FileTools.read_skill_file(read_input)
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_create_file_in_nested_dir(sample_skill, temp_skills_dir):
    """Test creating a file in a nested directory."""
    import time
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        # Use timestamp for unique filename
        unique_name = f"nested_file_{int(time.time() * 1000000)}.md"
        create_input = CreateSkillFileInput(
            skill_name="test-skill",
            file_path=f"docs/nested/{unique_name}",
            content="nested file"
        )
        result = await FileTools.create_skill_file(create_input)
        assert "Successfully created" in result[0].text
        
        # Verify we can read it
        read_input = ReadSkillFileInput(skill_name="test-skill", file_path=f"docs/nested/{unique_name}")
        result = await FileTools.read_skill_file(read_input)
        assert "nested file" in result[0].text


@pytest.mark.asyncio
async def test_update_nonexistent_file(sample_skill, temp_skills_dir):
    """Test updating a nonexistent file."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        update_input = UpdateSkillFileInput(
            skill_name="test-skill",
            file_path="nonexistent.txt",
            content="content"
        )
        result = await FileTools.update_skill_file(update_input)
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_delete_nonexistent_file(sample_skill, temp_skills_dir):
    """Test deleting a nonexistent file."""
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        delete_input = DeleteSkillFileInput(
            skill_name="test-skill",
            file_path="nonexistent.txt"
        )
        result = await FileTools.delete_skill_file(delete_input)
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_create_file_with_large_content(sample_skill, temp_skills_dir):
    """Test creating a file with large content."""
    import time
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        large_content = "x" * 10000
        # Use timestamp for unique filename
        unique_name = f"large_{int(time.time() * 1000000)}.txt"
        create_input = CreateSkillFileInput(
            skill_name="test-skill",
            file_path=unique_name,
            content=large_content
        )
        result = await FileTools.create_skill_file(create_input)
        assert "10000 characters" in result[0].text


@pytest.mark.asyncio
async def test_run_skill_script(sample_skill, temp_skills_dir):
    """Test run_skill_script tool with invalid script."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        input_data = RunSkillScriptInput(
            skill_name="test-skill",
            script_path="scripts/nonexistent.py"
        )
        result = await ScriptTools.run_skill_script(input_data)
        
        assert len(result) > 0
        # Should handle error gracefully
        assert "Error" in result[0].text or "does not exist" in result[0].text


@pytest.mark.asyncio
async def test_run_shell_script_tool_error(sample_skill, temp_skills_dir):
    """Test running a shell script through tools with error."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        input_data = RunSkillScriptInput(
            skill_name="test-skill",
            script_path="scripts/nonexistent.sh"
        )
        result = await ScriptTools.run_skill_script(input_data)
        
        assert len(result) > 0
        assert "Error" in result[0].text or "does not exist" in result[0].text


@pytest.mark.asyncio
async def test_run_script_with_args_error(sample_skill, temp_skills_dir):
    """Test running script with arguments but script doesn't exist."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        input_data = RunSkillScriptInput(
            skill_name="test-skill",
            script_path="scripts/nonexistent.py",
            args=["arg1", "arg2"]
        )
        result = await ScriptTools.run_skill_script(input_data)
        
        assert len(result) > 0
        assert "Error" in result[0].text or "does not exist" in result[0].text


@pytest.mark.asyncio
async def test_read_skill_env(skill_with_env, temp_skills_dir):
    """Test read_skill_env tool."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        input_data = ReadSkillEnvInput(skill_name="test-skill")
        result = await ScriptTools.read_skill_env(input_data)
        
        assert len(result) > 0
        text = result[0].text
        assert "API_KEY" in text
        assert "DATABASE_URL" in text


@pytest.mark.asyncio
async def test_read_skill_env_empty(sample_skill, temp_skills_dir):
    """Test read_skill_env with no environment variables."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        input_data = ReadSkillEnvInput(skill_name="test-skill")
        result = await ScriptTools.read_skill_env(input_data)
        
        assert len(result) > 0
        text = result[0].text
        assert "No environment variables" in text


@pytest.mark.asyncio
async def test_update_skill_env(sample_skill, temp_skills_dir):
    """Test update_skill_env tool."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        input_data = UpdateSkillEnvInput(
            skill_name="test-skill",
            content="NEW_VAR=value\nANOTHER=test"
        )
        result = await ScriptTools.update_skill_env(input_data)
        
        assert "Successfully updated" in result[0].text
        
        # Verify it was updated
        read_input = ReadSkillEnvInput(skill_name="test-skill")
        read_result = await ScriptTools.read_skill_env(read_input)
        assert "NEW_VAR" in read_result[0].text


@pytest.mark.asyncio
async def test_get_script_tools_list():
    """Test get_script_tools returns all tools."""
    tools = ScriptTools.get_script_tools()
    
    assert len(tools) == 3
    tool_names = [t.name for t in tools]
    assert "run_skill_script" in tool_names
    assert "read_skill_env" in tool_names
    assert "update_skill_env" in tool_names


@pytest.mark.asyncio
async def test_server_list_tools():
    """Test MCP server list_tools endpoint."""
    from skill_mcp.server import list_tools
    
    tools = await list_tools()
    
    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    
    # Check all expected tools are present
    assert "list_skills" in tool_names
    assert "get_skill_details" in tool_names
    assert "read_skill_file" in tool_names
    assert "create_skill_file" in tool_names
    assert "update_skill_file" in tool_names
    assert "delete_skill_file" in tool_names
    assert "run_skill_script" in tool_names
    assert "read_skill_env" in tool_names
    assert "update_skill_env" in tool_names


@pytest.mark.asyncio
async def test_server_list_skills_tool(sample_skill, temp_skills_dir):
    """Test server call_tool for list_skills."""
    from skill_mcp.server import call_tool
    
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool("list_skills", {})
        
        assert len(result) > 0
        assert "test-skill" in result[0].text


@pytest.mark.asyncio
async def test_server_get_skill_details_tool(sample_skill, temp_skills_dir):
    """Test server call_tool for get_skill_details."""
    from skill_mcp.server import call_tool
    
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool("get_skill_details", {"skill_name": "test-skill"})
        
        assert len(result) > 0
        assert "test-skill" in result[0].text


@pytest.mark.asyncio
async def test_server_read_skill_file_tool(sample_skill, temp_skills_dir):
    """Test server call_tool for read_skill_file."""
    from skill_mcp.server import call_tool
    
    with patch("skill_mcp.services.file_service.SKILLS_DIR", temp_skills_dir):
        result = await call_tool(
            "read_skill_file",
            {"skill_name": "test-skill", "file_path": "SKILL.md"}
        )
        
        assert len(result) > 0
        assert "test-skill" in result[0].text


@pytest.mark.asyncio
async def test_server_unknown_tool():
    """Test server call_tool with unknown tool."""
    from skill_mcp.server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_server_call_tool_with_exception():
    """Test server call_tool handles exceptions."""
    from skill_mcp.server import call_tool
    
    # Call a tool with invalid arguments should be handled gracefully
    result = await call_tool("list_skills", {"invalid_arg": "value"})
    
    # Should return a result (might succeed if extra args are ignored, or error)
    assert len(result) > 0
    assert isinstance(result[0].text, str)


@pytest.mark.asyncio
async def test_get_file_tools_list():
    """Test get_file_tools returns all tools."""
    tools = FileTools.get_file_tools()
    
    assert len(tools) == 4
    tool_names = [t.name for t in tools]
    assert "read_skill_file" in tool_names
    assert "create_skill_file" in tool_names
    assert "update_skill_file" in tool_names
    assert "delete_skill_file" in tool_names


@pytest.mark.asyncio
async def test_get_skill_tools_list():
    """Test get_skill_tools returns all tools."""
    tools = SkillTools.get_list_tools()
    
    assert len(tools) == 2
    tool_names = [t.name for t in tools]
    assert "list_skills" in tool_names
    assert "get_skill_details" in tool_names
