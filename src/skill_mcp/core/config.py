"""Configuration constants for skill-mcp server."""

from pathlib import Path

# Directories
SKILLS_DIR = Path.home() / ".skill-mcp" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# File operation limits
MAX_FILE_SIZE = 1_000_000  # 1MB limit for file operations
MAX_OUTPUT_SIZE = 100_000  # 100KB limit for script output

# Script execution
SCRIPT_TIMEOUT_SECONDS = 30
DEFAULT_PYTHON_INTERPRETER = "python3"

# Environment variables
ENV_FILE_NAME = ".env"

# Skill structure
SKILL_METADATA_FILE = "SKILL.md"
