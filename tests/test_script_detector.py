"""Tests for script detection utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open


def test_get_file_type_python():
    """Test get_file_type for Python files."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("script.py")) == "python"


def test_get_file_type_shell():
    """Test get_file_type for shell scripts."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("script.sh")) == "shell"
    assert get_file_type(Path("script.bash")) == "shell"
    assert get_file_type(Path("script.zsh")) == "shell"


def test_get_file_type_markdown():
    """Test get_file_type for markdown files."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("README.md")) == "markdown"


def test_get_file_type_json():
    """Test get_file_type for JSON files."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("config.json")) == "json"


def test_get_file_type_yaml():
    """Test get_file_type for YAML files."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("config.yaml")) == "yaml"
    assert get_file_type(Path("config.yml")) == "yaml"


def test_get_file_type_unknown():
    """Test get_file_type for unknown files."""
    from skill_mcp.utils.script_detector import get_file_type
    
    assert get_file_type(Path("file.xyz")) == "unknown"
    assert get_file_type(Path("file")) == "unknown"


def test_is_executable_script_python(tmp_path):
    """Test is_executable_script for Python files."""
    from skill_mcp.utils.script_detector import is_executable_script
    
    script = tmp_path / "script.py"
    script.write_text("print('hello')")
    
    assert is_executable_script(script) is True


def test_is_executable_script_shell(tmp_path):
    """Test is_executable_script for shell scripts."""
    from skill_mcp.utils.script_detector import is_executable_script
    
    script = tmp_path / "script.sh"
    script.write_text("#!/bin/bash\necho 'hello'")
    
    assert is_executable_script(script) is True


def test_is_executable_script_shebang(tmp_path):
    """Test is_executable_script detects shebang."""
    from skill_mcp.utils.script_detector import is_executable_script
    
    script = tmp_path / "script.txt"
    script.write_text("#!/usr/bin/python3\nprint('hello')")
    
    assert is_executable_script(script) is True


def test_is_executable_script_non_executable(tmp_path):
    """Test is_executable_script for non-executable files."""
    from skill_mcp.utils.script_detector import is_executable_script
    
    script = tmp_path / "file.txt"
    script.write_text("just some text")
    
    assert is_executable_script(script) is False


def test_is_executable_script_permission(tmp_path):
    """Test is_executable_script detects executable permission."""
    from skill_mcp.utils.script_detector import is_executable_script
    import os
    
    script = tmp_path / "script"
    script.write_text("#!/bin/bash")
    os.chmod(script, 0o755)
    
    assert is_executable_script(script) is True


def test_has_uv_dependencies_with_script_metadata(tmp_path):
    """Test has_uv_dependencies detects PEP 723 script metadata."""
    from skill_mcp.utils.script_detector import has_uv_dependencies
    
    script = tmp_path / "script.py"
    script.write_text("""#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
print("hello")
""")
    
    assert has_uv_dependencies(script) is True


def test_has_uv_dependencies_with_pyproject(tmp_path):
    """Test has_uv_dependencies detects pyproject metadata."""
    from skill_mcp.utils.script_detector import has_uv_dependencies
    
    script = tmp_path / "script.py"
    script.write_text("""#!/usr/bin/env python3
# /// pyproject
# [project]
# dependencies = ["requests"]
# ///
print("hello")
""")
    
    assert has_uv_dependencies(script) is True


def test_has_uv_dependencies_without_metadata(tmp_path):
    """Test has_uv_dependencies returns False without metadata."""
    from skill_mcp.utils.script_detector import has_uv_dependencies
    
    script = tmp_path / "script.py"
    script.write_text("print('hello')")
    
    assert has_uv_dependencies(script) is False


def test_has_uv_dependencies_non_python(tmp_path):
    """Test has_uv_dependencies returns False for non-Python files."""
    from skill_mcp.utils.script_detector import has_uv_dependencies
    
    script = tmp_path / "script.sh"
    script.write_text("#!/bin/bash\necho hello")
    
    assert has_uv_dependencies(script) is False


def test_has_uv_dependencies_file_not_found(tmp_path):
    """Test has_uv_dependencies handles missing files."""
    from skill_mcp.utils.script_detector import has_uv_dependencies
    
    script = tmp_path / "nonexistent.py"
    
    assert has_uv_dependencies(script) is False


def test_list_executable_scripts(tmp_path):
    """Test list_executable_scripts finds executable scripts."""
    from skill_mcp.utils.script_detector import list_executable_scripts
    
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    
    # Create executable Python script
    py_script = scripts_dir / "test.py"
    py_script.write_text("print('hello')")
    
    # Create shell script
    sh_script = scripts_dir / "test.sh"
    sh_script.write_text("#!/bin/bash\necho hello")
    
    # Create non-executable file
    txt_file = scripts_dir / "readme.txt"
    txt_file.write_text("some text")
    
    scripts = list_executable_scripts(scripts_dir)
    
    assert len(scripts) == 2
    assert py_script in scripts
    assert sh_script in scripts
    assert txt_file not in scripts


def test_list_executable_scripts_nested(tmp_path):
    """Test list_executable_scripts finds nested scripts."""
    from skill_mcp.utils.script_detector import list_executable_scripts
    
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    nested = scripts_dir / "nested"
    nested.mkdir()
    
    py_script = nested / "test.py"
    py_script.write_text("print('hello')")
    
    scripts = list_executable_scripts(scripts_dir)
    
    assert py_script in scripts


def test_list_executable_scripts_empty_dir(tmp_path):
    """Test list_executable_scripts with empty directory."""
    from skill_mcp.utils.script_detector import list_executable_scripts
    
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    
    scripts = list_executable_scripts(scripts_dir)
    
    assert len(scripts) == 0


def test_list_executable_scripts_nonexistent_dir(tmp_path):
    """Test list_executable_scripts with nonexistent directory."""
    from skill_mcp.utils.script_detector import list_executable_scripts
    
    nonexistent = tmp_path / "nonexistent"
    
    scripts = list_executable_scripts(nonexistent)
    
    assert len(scripts) == 0
