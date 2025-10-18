"""Tests for script service."""

import pytest
import asyncio
from skill_mcp.services.script_service import ScriptService, ScriptResult
from skill_mcp.core.exceptions import ScriptExecutionError, PathTraversalError, InvalidPathError
from unittest.mock import patch


@pytest.mark.asyncio
async def test_run_nonexistent_script(sample_skill, temp_skills_dir):
    """Test running nonexistent script."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with pytest.raises(ScriptExecutionError):
            await ScriptService.run_script("test-skill", "scripts/nonexistent.py")


@pytest.mark.asyncio
async def test_script_result_to_dict():
    """Test ScriptResult.to_dict()."""
    result = ScriptResult(0, "output", "")
    data = result.to_dict()
    
    assert data["exit_code"] == 0
    assert data["stdout"] == "output"
    assert data["success"] is True


@pytest.mark.asyncio
async def test_script_result_failure():
    """Test ScriptResult with failure."""
    result = ScriptResult(1, "", "error output")
    data = result.to_dict()
    
    assert data["exit_code"] == 1
    assert data["stderr"] == "error output"
    assert data["success"] is False


@pytest.mark.asyncio
async def test_run_script_invalid_path(sample_skill, temp_skills_dir):
    """Test running a script with invalid path."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            with pytest.raises(InvalidPathError):
                await ScriptService.run_script("test-skill", "../../etc/passwd")


@pytest.mark.asyncio
async def test_run_script_directory_as_file(sample_skill, temp_skills_dir):
    """Test running a directory as a file."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            with pytest.raises(ScriptExecutionError):
                await ScriptService.run_script("test-skill", "scripts")


@pytest.mark.asyncio
async def test_script_result_with_truncated_output():
    """Test ScriptResult handles truncated output."""
    large_output = "x" * (1024 * 1024 + 100)  # Larger than MAX_OUTPUT_SIZE
    result = ScriptResult(0, large_output, "")
    
    # Output should be truncated in the service, but ScriptResult stores it
    assert len(result.stdout) > 0


@pytest.mark.asyncio
async def test_run_script_invalid_working_dir(sample_skill, temp_skills_dir):
    """Test running a script with invalid working directory."""
    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            with pytest.raises((InvalidPathError, PathTraversalError)):
                await ScriptService.run_script(
                    "test-skill",
                    "scripts/test.py",
                    working_dir="../../etc"
                )
