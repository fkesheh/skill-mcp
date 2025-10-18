"""Tests for path validation utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch
from skill_mcp.utils.path_utils import validate_path
from skill_mcp.core.exceptions import PathTraversalError, InvalidPathError


def test_validate_valid_path(temp_skills_dir):
    """Test validating a valid path."""
    with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
        skill_name = "test-skill"
        file_path = "scripts/test.py"
        
        # Create skill directory
        skill_dir = temp_skills_dir / skill_name
        skill_dir.mkdir()
        
        result = validate_path(skill_name, file_path)
        
        assert result.parent.parent.name == skill_name
        assert result.name == "test.py"


def test_validate_path_with_parent_traversal(temp_skills_dir):
    """Test that parent directory traversal is blocked."""
    with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
        skill_name = "test-skill"
        
        # Create skill directory
        skill_dir = temp_skills_dir / skill_name
        skill_dir.mkdir()
        
        with pytest.raises(PathTraversalError):
            validate_path(skill_name, "../../../etc/passwd")


def test_validate_path_with_absolute_path(temp_skills_dir):
    """Test that absolute paths are blocked."""
    with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
        skill_name = "test-skill"
        
        # Create skill directory
        skill_dir = temp_skills_dir / skill_name
        skill_dir.mkdir()
        
        with pytest.raises(PathTraversalError):
            validate_path(skill_name, "/etc/passwd")


def test_validate_nested_path(temp_skills_dir):
    """Test validating nested paths."""
    with patch("skill_mcp.utils.path_utils.SKILLS_DIR", temp_skills_dir):
        skill_name = "test-skill"
        file_path = "references/docs/nested/file.md"
        
        # Create skill directory
        skill_dir = temp_skills_dir / skill_name
        skill_dir.mkdir()
        
        result = validate_path(skill_name, file_path)
        
        assert "references" in str(result)
        assert "nested" in str(result)
