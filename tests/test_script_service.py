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


@pytest.mark.asyncio
async def test_execute_python_code_loads_env_vars_from_referenced_skills(tmp_path):
    """Test execute_python_code loads environment variables from referenced skills."""
    # Create a skill with a .env file
    skill_dir = tmp_path / "api-skill"
    skill_dir.mkdir()

    # Create SKILL.md
    (skill_dir / "SKILL.md").write_text("# API Skill\n\nA skill with API credentials")

    # Create .env file with test variables
    env_file = skill_dir / ".env"
    env_file.write_text("API_KEY=test-secret-key-123\nAPI_URL=https://api.example.com")

    # Create a module that uses environment variables
    lib_file = skill_dir / "api_client.py"
    lib_file.write_text("""import os

def get_api_key():
    return os.environ.get('API_KEY', 'not-found')

def get_api_url():
    return os.environ.get('API_URL', 'not-found')
""")

    # Test code that imports and uses the env vars
    code = """from api_client import get_api_key, get_api_url

api_key = get_api_key()
api_url = get_api_url()
print(f"API_KEY: {api_key}")
print(f"API_URL: {api_url}")
"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        with patch("skill_mcp.services.env_service.SKILLS_DIR", tmp_path):
            result = await ScriptService.execute_python_code(
                code, skill_references=["api-skill:api_client.py"]
            )

            assert result.exit_code == 0
            assert "API_KEY: test-secret-key-123" in result.stdout
            assert "API_URL: https://api.example.com" in result.stdout


@pytest.mark.asyncio
async def test_execute_python_code_loads_env_from_multiple_skills(tmp_path):
    """Test execute_python_code loads env vars from multiple referenced skills."""
    # Create first skill with env vars
    skill1_dir = tmp_path / "skill1"
    skill1_dir.mkdir()
    (skill1_dir / "SKILL.md").write_text("# Skill 1")
    (skill1_dir / ".env").write_text("VAR1=value1\nSHARED=from_skill1")
    (skill1_dir / "module1.py").write_text(
        "import os\ndef get_var1(): return os.environ.get('VAR1', 'not-found')"
    )

    # Create second skill with env vars
    skill2_dir = tmp_path / "skill2"
    skill2_dir.mkdir()
    (skill2_dir / "SKILL.md").write_text("# Skill 2")
    (skill2_dir / ".env").write_text("VAR2=value2\nSHARED=from_skill2")
    (skill2_dir / "module2.py").write_text(
        "import os\ndef get_var2(): return os.environ.get('VAR2', 'not-found')"
    )

    # Test code that uses env vars from both skills
    code = """import os
from module1 import get_var1
from module2 import get_var2

print(f"VAR1: {get_var1()}")
print(f"VAR2: {get_var2()}")
print(f"SHARED: {os.environ.get('SHARED', 'not-found')}")
"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        with patch("skill_mcp.services.env_service.SKILLS_DIR", tmp_path):
            result = await ScriptService.execute_python_code(
                code, skill_references=["skill1:module1.py", "skill2:module2.py"]
            )

            assert result.exit_code == 0
            assert "VAR1: value1" in result.stdout
            assert "VAR2: value2" in result.stdout
            # The last skill's env var should win in case of conflicts
            assert "SHARED: from_skill2" in result.stdout


@pytest.mark.asyncio
async def test_execute_python_code_handles_missing_env_file(tmp_path):
    """Test execute_python_code works even if referenced skill has no .env file."""
    # Create skill without .env file
    skill_dir = tmp_path / "no-env-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# No Env Skill")
    (skill_dir / "utils.py").write_text("def add(a, b): return a + b")

    code = """from utils import add
result = add(10, 20)
print(f"Result: {result}")
"""

    with patch("skill_mcp.services.script_service.SKILLS_DIR", tmp_path):
        result = await ScriptService.execute_python_code(
            code, skill_references=["no-env-skill:utils.py"]
        )

        assert result.exit_code == 0
        assert "Result: 30" in result.stdout
