"""Pydantic models for skill-mcp MCP tools."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Input Models

class ListSkillsInput(BaseModel):
    """Input for listing all skills."""
    pass


class GetSkillDetailsInput(BaseModel):
    """Input for getting detailed skill information."""
    skill_name: str = Field(description="Name of the skill")


class ReadSkillFileInput(BaseModel):
    """Input for reading a skill file."""
    skill_name: str = Field(description="Name of the skill")
    file_path: str = Field(
        description="Relative path to the file within the skill directory (e.g., 'SKILL.md' or 'scripts/process.py')"
    )


class CreateSkillFileInput(BaseModel):
    """Input for creating a new skill file."""
    skill_name: str = Field(description="Name of the skill")
    file_path: str = Field(
        description="Relative path for the new file within the skill directory"
    )
    content: str = Field(description="Content to write to the file")


class UpdateSkillFileInput(BaseModel):
    """Input for updating an existing skill file."""
    skill_name: str = Field(description="Name of the skill")
    file_path: str = Field(
        description="Relative path to the file within the skill directory"
    )
    content: str = Field(description="New file content")


class DeleteSkillFileInput(BaseModel):
    """Input for deleting a skill file."""
    skill_name: str = Field(description="Name of the skill")
    file_path: str = Field(
        description="Relative path to the file to delete within the skill directory"
    )


class RunSkillScriptInput(BaseModel):
    """Input for running a skill script."""
    skill_name: str = Field(description="Name of the skill")
    script_path: str = Field(
        description="Relative path to the script within the skill directory"
    )
    args: Optional[List[str]] = Field(
        default=None,
        description="Optional command-line arguments to pass to the script"
    )
    working_dir: Optional[str] = Field(
        default=None,
        description="Optional working directory for script execution"
    )


class ReadSkillEnvInput(BaseModel):
    """Input for reading skill .env file."""
    skill_name: str = Field(description="Name of the skill")


class UpdateSkillEnvInput(BaseModel):
    """Input for updating skill .env file."""
    skill_name: str = Field(description="Name of the skill")
    content: str = Field(description=".env file content")


# Output Models

class FileInfo(BaseModel):
    """Information about a file."""
    path: str
    size: int
    type: str  # 'python', 'shell', 'markdown', 'unknown'
    is_executable: bool = False
    has_uv_deps: Optional[bool] = None  # Only for Python scripts


class ScriptInfo(BaseModel):
    """Information about an executable script."""
    path: str
    type: str  # 'python', 'shell'
    has_uv_deps: bool = False


class SkillMetadata(BaseModel):
    """Metadata extracted from SKILL.md YAML frontmatter."""
    name: Optional[str] = None
    description: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class SkillDetails(BaseModel):
    """Comprehensive skill information."""
    name: str
    description: str
    metadata: SkillMetadata
    files: List[FileInfo]
    scripts: List[ScriptInfo]
    env_vars: List[str]  # Environment variable names only
    has_env_file: bool
    skill_md_content: Optional[str] = None  # Full SKILL.md content


class SkillSummary(BaseModel):
    """Lightweight skill summary for listing."""
    name: str
    description: str
    path: str
    has_skill_md: bool
