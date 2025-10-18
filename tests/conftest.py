"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_skills_dir(tmp_path, monkeypatch):
    """Create a temporary skills directory for testing with monkeypatch."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    
    # Use monkeypatch to set SKILLS_DIR in all modules
    import skill_mcp.core.config as config_mod
    import skill_mcp.services.file_service as file_mod
    import skill_mcp.services.skill_service as skill_mod
    import skill_mcp.services.script_service as script_mod
    import skill_mcp.services.env_service as env_mod
    
    monkeypatch.setattr(config_mod, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(file_mod, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(skill_mod, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(script_mod, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(env_mod, "SKILLS_DIR", skills_dir)
    
    return skills_dir


@pytest.fixture
def sample_skill(temp_skills_dir):
    """Create a sample skill with SKILL.md and scripts."""
    skill_dir = temp_skills_dir / "test-skill"
    skill_dir.mkdir()
    
    # Create SKILL.md with frontmatter
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""---
name: test-skill
description: A test skill for unit testing
---

# Test Skill

This is a test skill.
""")
    
    # Create scripts directory
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    
    # Create a Python script
    py_script = scripts_dir / "test.py"
    py_script.write_text("""#!/usr/bin/env python3
print("Hello from test script")
""")
    py_script.chmod(0o755)
    
    # Create a shell script
    sh_script = scripts_dir / "test.sh"
    sh_script.write_text("""#!/bin/bash
echo "Hello from shell script"
""")
    sh_script.chmod(0o755)
    
    # Create a Python script with uv deps
    py_deps_script = scripts_dir / "with_deps.py"
    py_deps_script.write_text("""#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
print("Script with deps")
""")
    py_deps_script.chmod(0o755)
    
    return skill_dir


@pytest.fixture
def skill_with_env(sample_skill):
    """Create a skill with .env file."""
    env_file = sample_skill / ".env"
    env_file.write_text("API_KEY=test-key\nDATABASE_URL=postgresql://localhost/db\n")
    return sample_skill
