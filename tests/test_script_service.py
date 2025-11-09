"""Tests for script service."""

from unittest.mock import patch

import pytest

from skill_mcp.core.exceptions import InvalidPathError, PathTraversalError, ScriptExecutionError
from skill_mcp.services.script_service import (
    ScriptResult,
    ScriptService,
    extract_pep723_dependencies,
    merge_dependencies,
)


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
                    "test-skill", "scripts/test.py", working_dir="../../etc"
                )


# Tests for dependency aggregation features


def test_extract_pep723_dependencies_with_deps():
    """Test extracting dependencies from PEP 723 metadata."""
    code = """#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "pandas>=2.0.0",
# ]
# ///

import requests
"""
    deps = extract_pep723_dependencies(code)
    assert deps == ["requests>=2.31.0", "pandas>=2.0.0"]


def test_extract_pep723_dependencies_no_deps():
    """Test extracting dependencies when none exist."""
    code = """#!/usr/bin/env python3
# /// script
# ///

import os
"""
    deps = extract_pep723_dependencies(code)
    assert deps == []


def test_extract_pep723_dependencies_no_metadata():
    """Test extracting dependencies when no PEP 723 block exists."""
    code = """#!/usr/bin/env python3

import os
"""
    deps = extract_pep723_dependencies(code)
    assert deps == []


def test_merge_dependencies_creates_new_block():
    """Test merging dependencies creates PEP 723 block when none exists."""
    code = """from utils import calculate

print(calculate(10, 20))
"""
    merged = merge_dependencies(code, ["requests>=2.31.0", "pandas>=2.0.0"])

    assert "# /// script" in merged
    assert "# ///" in merged
    assert "requests>=2.31.0" in merged
    assert "pandas>=2.0.0" in merged
    assert "from utils import calculate" in merged


def test_merge_dependencies_merges_with_existing():
    """Test merging dependencies with existing PEP 723 block."""
    code = """# /// script
# dependencies = [
#   "rich>=13.0.0",
# ]
# ///

from utils import calculate
"""
    merged = merge_dependencies(code, ["requests>=2.31.0"])

    assert "rich>=13.0.0" in merged
    assert "requests>=2.31.0" in merged
    assert "from utils import calculate" in merged


def test_merge_dependencies_deduplicates():
    """Test merging dependencies deduplicates same package."""
    code = """# /// script
# dependencies = [
#   "requests>=2.30.0",
# ]
# ///

print("test")
"""
    merged = merge_dependencies(code, ["requests>=2.31.0"])

    # Should keep the later version
    assert "requests>=2.31.0" in merged
    assert "requests>=2.30.0" not in merged


def test_merge_dependencies_empty_list():
    """Test merging with empty dependency list returns original code."""
    code = """print("test")"""
    merged = merge_dependencies(code, [])

    assert merged == code


@pytest.mark.asyncio
async def test_execute_python_code_with_skill_references(tmp_path):
    """Test execute_python_code with skill references that have PEP 723 deps."""
    # Create a temporary skill with a module that has PEP 723 deps
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    # Create SKILL.md
    (skill_dir / "SKILL.md").write_text("# Test Skill\n\nA test skill")

    # Create a module with PEP 723 dependencies
    lib_file = skill_dir / "lib_with_deps.py"
    lib_file.write_text("""#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

import requests

def fetch_data(url):
    response = requests.get(url, timeout=10)
    return response.json()
""")

    # Test code that imports from the module
    code = """from lib_with_deps import fetch_data

url = "https://jsonplaceholder.typicode.com/todos/1"
data = fetch_data(url)
print(f"Success: {data['id']}")
"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        result = await ScriptService.execute_python_code(
            code, skill_references=["test-skill:lib_with_deps.py"]
        )

        assert result.exit_code == 0
        assert "Success:" in result.stdout


# Tests for timeout functionality


@pytest.mark.asyncio
async def test_run_script_with_custom_timeout(sample_skill, temp_skills_dir):
    """Test run_script uses custom timeout when provided."""
    # Create a simple script
    script_path = temp_skills_dir / "test-skill" / "quick.py"
    script_path.write_text("print('done')")

    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            # Should complete within custom timeout
            result = await ScriptService.run_script("test-skill", "quick.py", timeout=60)
            assert result.exit_code == 0
            assert "done" in result.stdout


@pytest.mark.asyncio
async def test_run_script_with_default_timeout(sample_skill, temp_skills_dir):
    """Test run_script uses default timeout when not provided."""
    # Create a simple script
    script_path = temp_skills_dir / "test-skill" / "quick.py"
    script_path.write_text("print('done')")

    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            # Should use default timeout (30 seconds)
            result = await ScriptService.run_script("test-skill", "quick.py")
            assert result.exit_code == 0
            assert "done" in result.stdout


@pytest.mark.asyncio
async def test_run_script_timeout_error_message(sample_skill, temp_skills_dir):
    """Test timeout error message includes the correct timeout value."""
    # Create a script that sleeps forever
    script_path = temp_skills_dir / "test-skill" / "slow.py"
    script_path.write_text("import time; time.sleep(999)")

    with patch("skill_mcp.services.script_service.SKILLS_DIR", temp_skills_dir):
        with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
            # Test with custom timeout of 1 second
            with pytest.raises(ScriptExecutionError) as exc_info:
                await ScriptService.run_script("test-skill", "slow.py", timeout=1)

            # Error message should mention the custom timeout
            assert "1 seconds" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_python_code_with_custom_timeout(tmp_path):
    """Test execute_python_code uses custom timeout when provided."""
    code = """print('done')"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        result = await ScriptService.execute_python_code(code, timeout=60)
        assert result.exit_code == 0
        assert "done" in result.stdout


@pytest.mark.asyncio
async def test_execute_python_code_timeout_error_message(tmp_path):
    """Test execute_python_code timeout error includes correct timeout value."""
    code = """import time; time.sleep(999)"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        with pytest.raises(ScriptExecutionError) as exc_info:
            await ScriptService.execute_python_code(code, timeout=1)

        # Error message should mention the custom timeout
        assert "1 seconds" in str(exc_info.value)
