"""Pydantic models for skill-mcp MCP tools."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
    file_path: str = Field(description="Relative path for the new file within the skill directory")
    content: str = Field(description="Content to write to the file")


class UpdateSkillFileInput(BaseModel):
    """Input for updating an existing skill file."""

    skill_name: str = Field(description="Name of the skill")
    file_path: str = Field(description="Relative path to the file within the skill directory")
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
    script_path: str = Field(description="Relative path to the script within the skill directory")
    args: Optional[List[str]] = Field(
        default=None, description="Optional command-line arguments to pass to the script"
    )
    working_dir: Optional[str] = Field(
        default=None, description="Optional working directory for script execution"
    )
    timeout: Optional[int] = Field(
        default=None,
        description="Optional timeout in seconds (defaults to 30 seconds if not specified)",
    )


class ExecutePythonCodeInput(BaseModel):
    """Input for executing Python code directly."""

    code: str = Field(description="Python code to execute (can include PEP 723 dependencies)")
    skill_references: Optional[List[str]] = Field(
        default=None,
        description="Optional list of skill files to import using namespace format (e.g., 'calculator:utils.py')",
    )
    timeout: Optional[int] = Field(
        default=None,
        description="Optional timeout in seconds (defaults to 30 seconds if not specified)",
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
    modified: Optional[float] = None  # Unix timestamp (from st_mtime)


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
    has_skill_md: bool


# ===================
# Graph Models
# ===================


class NodeType(str, Enum):
    """Types of nodes in the graph."""

    SKILL = "Skill"
    KNOWLEDGE = "Knowledge"
    SCRIPT = "Script"
    TOOL = "Tool"


class RelationshipType(str, Enum):
    """Types of relationships between nodes."""

    CONTAINS = "CONTAINS"  # Skill contains Script/Knowledge
    DEPENDS_ON = "DEPENDS_ON"  # Script depends on another Script/Tool
    USES = "USES"  # Script uses Tool
    REFERENCES = "REFERENCES"  # Knowledge references Skill/Script
    RELATED_TO = "RELATED_TO"  # Knowledge related to Knowledge
    EXPLAINS = "EXPLAINS"  # Knowledge explains Skill
    IMPORTS = "IMPORTS"  # Script imports module/library


class Node(BaseModel):
    """Generic node in the knowledge graph."""

    id: str = Field(description="Unique node identifier")
    type: NodeType = Field(description="Type of node")
    name: str = Field(description="Display name")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Type-specific properties")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class Relationship(BaseModel):
    """Relationship between two nodes."""

    from_id: str = Field(description="Source node ID")
    to_id: str = Field(description="Target node ID")
    type: RelationshipType = Field(description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship-specific properties")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        """Pydantic config."""

        use_enum_values = True
