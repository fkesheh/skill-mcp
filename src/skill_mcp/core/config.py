"""Configuration constants for skill-mcp server."""

import os
from pathlib import Path

# Directories
# Allow override via SKILL_MCP_DIR environment variable
_default_skills_dir = Path.home() / ".skill-mcp" / "skills"
SKILLS_DIR = Path(os.getenv("SKILL_MCP_DIR", str(_default_skills_dir)))
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

# Neo4j Graph Database Configuration
# Enable graph features via SKILL_MCP_GRAPH_ENABLED environment variable
GRAPH_ENABLED = os.getenv("SKILL_MCP_GRAPH_ENABLED", "false").lower() == "true"
GRAPH_AUTO_SYNC = os.getenv("SKILL_MCP_GRAPH_AUTO_SYNC", "true").lower() == "true"

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Graph operation limits
GRAPH_MAX_TRAVERSAL_DEPTH = int(os.getenv("GRAPH_MAX_TRAVERSAL_DEPTH", "5"))
GRAPH_QUERY_TIMEOUT = int(os.getenv("GRAPH_QUERY_TIMEOUT", "30"))  # seconds
