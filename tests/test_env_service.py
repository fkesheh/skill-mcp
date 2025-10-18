"""Tests for environment service."""

import pytest
from unittest.mock import patch
from skill_mcp.services.env_service import EnvironmentService
from skill_mcp.core.exceptions import SkillNotFoundError, EnvFileError


def test_load_skill_env_empty(sample_skill, temp_skills_dir):
    """Test loading env when no .env file exists."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        env = EnvironmentService.load_skill_env("test-skill")
        assert env == {}


def test_load_skill_env_with_vars(skill_with_env, temp_skills_dir):
    """Test loading env variables from .env file."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        env = EnvironmentService.load_skill_env("test-skill")
        
        assert "API_KEY" in env
        assert env["API_KEY"] == "test-key"
        assert "DATABASE_URL" in env


def test_load_skill_env_nonexistent_skill(temp_skills_dir):
    """Test loading env for nonexistent skill."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        with pytest.raises(SkillNotFoundError):
            EnvironmentService.load_skill_env("nonexistent")


def test_read_env_file_empty(sample_skill, temp_skills_dir):
    """Test reading empty .env file."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        content = EnvironmentService.read_env_file("test-skill")
        assert content == ""


def test_read_env_file(skill_with_env, temp_skills_dir):
    """Test reading .env file content."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        content = EnvironmentService.read_env_file("test-skill")
        
        assert "API_KEY=test-key" in content
        assert "DATABASE_URL=" in content


def test_update_env_file(sample_skill, temp_skills_dir):
    """Test updating .env file."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        new_content = "NEW_VAR=value\nANOTHER=another_value\n"
        EnvironmentService.update_env_file("test-skill", new_content)
        
        # Verify it was written
        read_content = EnvironmentService.read_env_file("test-skill")
        assert "NEW_VAR=value" in read_content


def test_get_env_keys(skill_with_env, temp_skills_dir):
    """Test getting environment variable keys."""
    with patch("skill_mcp.services.env_service.SKILLS_DIR", temp_skills_dir):
        keys = EnvironmentService.get_env_keys("test-skill")
        
        assert "API_KEY" in keys
        assert "DATABASE_URL" in keys
        assert len(keys) == 2
