"""Unified CRUD input models for skill-mcp MCP tools."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FileSpec(BaseModel):
    """Specification for a file to create/update."""

    path: str = Field(description="Relative path within skill directory")
    content: str = Field(description="File content")


class SkillCrudInput(BaseModel):
    """Unified input for skill CRUD operations."""

    operation: str = Field(
        description="Operation to perform: 'create', 'list', 'get', 'validate', 'delete'"
    )
    skill_name: Optional[str] = Field(
        default=None, description="Name of the skill (required for get, validate, delete, create)"
    )
    description: Optional[str] = Field(
        default=None, description="Skill description (optional for create)"
    )
    template: Optional[str] = Field(
        default="basic",
        description="Template to use for create: 'basic', 'python', 'bash', 'nodejs'",
    )
    search: Optional[str] = Field(
        default=None, description="Search pattern for list (text or regex)"
    )
    include_content: bool = Field(
        default=False, description="Include SKILL.md content in get operation"
    )
    confirm: bool = Field(
        default=False, description="Confirm delete operation (required for delete)"
    )


class SkillFilesCrudInput(BaseModel):
    """Unified input for skill file CRUD operations."""

    operation: str = Field(description="Operation to perform: 'read', 'create', 'update', 'delete'")
    skill_name: str = Field(description="Name of the skill")

    # Single file operations
    file_path: Optional[str] = Field(
        default=None, description="Relative path to file (for single file operations)"
    )
    content: Optional[str] = Field(
        default=None, description="File content (for single create/update)"
    )

    # Bulk file operations
    files: Optional[List[FileSpec]] = Field(
        default=None, description="List of files for bulk create/update operations"
    )
    file_paths: Optional[List[str]] = Field(
        default=None, description="List of file paths for bulk read operations"
    )
    atomic: bool = Field(
        default=True, description="Atomic mode: rollback all on error (for bulk create)"
    )


class SkillEnvCrudInput(BaseModel):
    """Unified input for skill environment variable CRUD operations."""

    operation: str = Field(description="Operation to perform: 'read', 'set', 'delete', 'clear'")
    skill_name: str = Field(description="Name of the skill")

    # Set operations (single or bulk)
    variables: Optional[Dict[str, str]] = Field(
        default=None, description="Variables to set (key-value pairs for 'set' operation)"
    )

    # Delete operations (single or bulk)
    keys: Optional[List[str]] = Field(
        default=None, description="Variable keys to delete (for 'delete' operation)"
    )


class GraphCrudInput(BaseModel):
    """Unified input for graph CRUD operations."""

    operation: str = Field(
        description="Operation to perform: 'sync', 'query', 'analyze', 'visualize', 'search', 'stats'"
    )

    # Sync operations
    skill_name: Optional[str] = Field(
        default=None, description="Skill name (for sync, analyze, query operations)"
    )
    sync_all: bool = Field(
        default=False, description="Sync all skills to graph (for 'sync' operation)"
    )
    delete_skill: bool = Field(
        default=False, description="Delete skill from graph (for 'sync' operation with skill_name)"
    )

    # Query operations
    cypher_query: Optional[str] = Field(
        default=None, description="Raw Cypher query string (for advanced users in 'query' operation)"
    )
    query_type: Optional[str] = Field(
        default=None,
        description="Predefined query type: 'related_skills', 'dependency_tree', 'skills_using_package', 'circular_deps', 'most_used_deps', 'orphaned_skills', 'complexity', 'imports', 'similar_skills', 'conflicts', 'execution_history', 'neighborhood'",
    )
    depth: int = Field(default=2, description="Traversal depth for relationship queries (1-5)")
    package_name: Optional[str] = Field(
        default=None, description="Package name for dependency queries"
    )
    limit: int = Field(default=20, description="Result limit for queries")

    # Visualization operations
    format: str = Field(
        default="json", description="Output format for visualize: 'json', 'cytoscape', 'summary'"
    )

    # Search operations
    search_query: Optional[str] = Field(
        default=None, description="Search text for full-text search across skills"
    )
    node_type: Optional[str] = Field(
        default="Skill", description="Node type to search: 'Skill', 'File', 'Dependency'"
    )
