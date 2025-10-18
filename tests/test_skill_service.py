"""Tests for skill service."""

import pytest
from unittest.mock import patch
from skill_mcp.services.skill_service import SkillService
from skill_mcp.core.exceptions import SkillNotFoundError


def test_list_skills_empty(temp_skills_dir):
    """Test listing skills when directory is empty."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        skills = SkillService.list_skills()
        assert len(skills) == 0


def test_list_skills_with_skill(sample_skill, temp_skills_dir):
    """Test listing skills."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        skills = SkillService.list_skills()
        
        assert len(skills) > 0
        assert skills[0].name == "test-skill"
        assert skills[0].has_skill_md


def test_get_skill_details(sample_skill, temp_skills_dir):
    """Test getting skill details."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        details = SkillService.get_skill_details("test-skill")
        
        assert details.name == "test-skill"
        assert details.description == "A test skill for unit testing"
        assert len(details.files) > 0
        assert len(details.scripts) > 0
        assert details.skill_md_content is not None
        assert "---" in details.skill_md_content  # Has frontmatter
        assert "test-skill" in details.skill_md_content
        assert "A test skill for unit testing" in details.skill_md_content
        assert "# Test Skill" in details.skill_md_content


def test_get_skill_details_with_env(skill_with_env, temp_skills_dir):
    """Test getting skill details with .env file."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        details = SkillService.get_skill_details("test-skill")
        
        assert details.has_env_file
        assert "API_KEY" in details.env_vars
        assert "DATABASE_URL" in details.env_vars


def test_get_nonexistent_skill(temp_skills_dir):
    """Test getting details for nonexistent skill."""
    with patch("skill_mcp.services.skill_service.SKILLS_DIR", temp_skills_dir):
        with pytest.raises(SkillNotFoundError):
            SkillService.get_skill_details("nonexistent")
