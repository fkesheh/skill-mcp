"""Tests for file service."""

import pytest
from skill_mcp.services.file_service import FileService
from skill_mcp.core.exceptions import FileNotFoundError, SkillNotFoundError


def test_list_skill_files_nonexistent_skill(temp_skills_dir, monkeypatch):
    """Test listing files for nonexistent skill."""
    with pytest.raises(SkillNotFoundError):
        FileService.list_skill_files("nonexistent-skill")


def test_read_nonexistent_file(sample_skill, temp_skills_dir):
    """Test reading nonexistent file."""
    with pytest.raises(FileNotFoundError):
        FileService.read_file("test-skill", "nonexistent.txt")


def test_delete_nonexistent_file(sample_skill, temp_skills_dir):
    """Test deleting nonexistent file."""
    with pytest.raises(FileNotFoundError):
        FileService.delete_file("test-skill", "nonexistent.txt")


def test_list_skill_files_has_files(sample_skill, temp_skills_dir):
    """Test listing files returns results."""
    files = FileService.list_skill_files("test-skill")
    assert len(files) > 0
    assert any("SKILL.md" in f["path"] for f in files)
