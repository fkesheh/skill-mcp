"""Unified CRUD input models for skill-mcp MCP tools."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from skill_mcp.models import NodeType, RelationshipType


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
    """Unified input for graph CRUD operations (skills and knowledge)."""

    operation: str = Field(
        description="Operation to perform: 'sync', 'query', 'analyze', 'visualize', 'search', 'stats', 'knowledge'"
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
        default=None,
        description="Raw Cypher query string (for advanced users in 'query' operation)",
    )
    query_type: Optional[str] = Field(
        default=None,
        description="Predefined query type: 'related_skills', 'dependency_tree', 'skills_using_package', 'circular_deps', 'most_used_deps', 'orphaned_skills', 'complexity', 'imports', 'similar_skills', 'conflicts', 'execution_history', 'neighborhood', 'list_knowledge', 'knowledge_by_id', 'knowledge_by_category', 'knowledge_by_tag', 'knowledge_about_skill', 'skills_for_knowledge', 'related_knowledge', 'knowledge_network'",
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

    # Knowledge operations
    knowledge_action: Optional[str] = Field(
        default=None,
        description="Knowledge action: 'create', 'update', 'delete', 'get', 'list', 'link_to_skill', 'link_to_knowledge'",
    )
    knowledge_id: Optional[str] = Field(
        default=None, description="Knowledge document ID (for knowledge operations)"
    )
    knowledge_title: Optional[str] = Field(
        default=None, description="Title of knowledge document (for create/update)"
    )
    knowledge_content: Optional[str] = Field(
        default=None, description="Content of knowledge document (markdown)"
    )
    knowledge_category: Optional[str] = Field(
        default="note",
        description="Category: 'tutorial', 'guide', 'reference', 'note', 'article'",
    )
    knowledge_tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    knowledge_author: Optional[str] = Field(default=None, description="Author name")
    relationship_type: Optional[str] = Field(
        default="EXPLAINS",
        description="Relationship type for linking: 'EXPLAINS', 'REFERENCES', 'USES'",
    )
    target_knowledge_id: Optional[str] = Field(
        default=None, description="Target knowledge ID for knowledge-to-knowledge links"
    )
    category_filter: Optional[str] = Field(
        default=None, description="Category filter for knowledge queries"
    )
    tag_filter: Optional[str] = Field(default=None, description="Tag filter for knowledge queries")


# ===================
# Graph CRUD Input Models
# ===================


class NodeCrudInput(BaseModel):
    """Unified input for node CRUD operations."""

    operation: Literal["create", "read", "update", "delete", "list"] = Field(
        description="Operation: create, read, update, delete, list"
    )

    # For create/read/update/delete
    node_id: Optional[str] = Field(
        default=None,
        description="Unique node identifier (required for: read, update, delete; optional for: create - auto-generated if not provided)",
    )
    node_type: Optional[NodeType] = Field(
        default=None,
        description="Type of node: Skill, Knowledge, Script, Tool, EnvFile (required for: create; optional for: list as filter)",
    )

    # For create/update
    name: Optional[str] = Field(
        default=None,
        description="Node display name (required for: create; optional for: update)",
    )
    description: Optional[str] = Field(
        default=None, description="Human-readable description (optional for: create, update)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Categorization tags as array of strings (optional for: create, update). Example: ['web', 'scraping', 'api']",
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""Type-specific properties as key-value object (optional for: create, update).

        Examples by node type:
        - Skill: {"skill_path": "/path", "has_env_file": true}
        - Script: {"language": "python", "file_path": "/path/script.py", "is_executable": true}
        - Knowledge: {"file_path": "/path/doc.md", "category": "tutorial"}
        - Tool: {"tool_name": "my_tool", "version": "1.0"}
        - EnvFile: {"file_path": "/path/.env"} [required for EnvFile nodes]
        """,
    )

    # For list
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Filter criteria for list operation (optional)"
    )
    limit: int = Field(default=50, description="Maximum number of results (for list operation)")
    offset: int = Field(default=0, description="Offset for pagination (for list operation)")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags are non-empty strings."""
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError(
                f"tags must be an array of strings, got {type(v).__name__}. Example: ['web', 'api']"
            )

        for i, tag in enumerate(v):
            if not isinstance(tag, str):
                raise ValueError(
                    f"tags[{i}] must be a string, got {type(tag).__name__}. Example: ['web', 'api']"
                )
            if not tag.strip():
                raise ValueError(
                    f"tags[{i}] cannot be empty or whitespace. Example: ['web', 'api']"
                )

        return v

    @field_validator("properties")
    @classmethod
    def validate_properties(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate properties is a dict."""
        if v is None:
            return v

        if not isinstance(v, dict):
            raise ValueError(
                f"properties must be an object (key-value pairs), got {type(v).__name__}. "
                'Example: {{"file_path": "/path/to/file", "language": "python"}}'
            )

        return v


class RelationshipCrudInput(BaseModel):
    """Unified input for relationship CRUD operations."""

    operation: Literal["create", "get", "delete", "list"] = Field(
        description="Operation: create, get, delete, list"
    )

    # For create/delete
    from_id: Optional[str] = Field(
        default=None,
        description="Source node ID (required for: create, delete)",
    )
    to_id: Optional[str] = Field(
        default=None,
        description="Target node ID (required for: create, delete)",
    )
    relationship_type: Optional[RelationshipType] = Field(
        default=None,
        description="Type of relationship: CONTAINS, DEPENDS_ON, USES, REFERENCES, RELATED_TO, EXPLAINS, IMPORTS, USES_ENV (required for: create, delete; optional for: get as filter)",
    )

    # For create
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description='Relationship-specific properties as key-value object (optional for: create). Example: {"reason": "imports helper functions"}',
    )

    # For get
    node_id: Optional[str] = Field(
        default=None,
        description="Node ID to get relationships for (required for: get)",
    )
    direction: Optional[Literal["incoming", "outgoing", "both"]] = Field(
        default="both",
        description="Direction of relationships to retrieve (optional for: get). Default: both",
    )

    # For list
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Filter criteria (optional for: list)"
    )
    limit: int = Field(default=50, description="Maximum number of results (for list operation)")


class QueryGraphInput(BaseModel):
    """Unified input for graph query operations."""

    operation: Literal["query", "traverse", "find_path", "stats"] = Field(
        description="Operation: query (Cypher), traverse, find_path, stats"
    )

    # For query (raw Cypher)
    cypher_query: Optional[str] = Field(default=None, description="Raw Cypher query string")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")

    # For traverse
    start_node_id: Optional[str] = Field(default=None, description="Starting node ID for traversal")
    direction: Optional[Literal["incoming", "outgoing", "both"]] = Field(
        default="both", description="Traversal direction"
    )
    max_depth: int = Field(default=3, description="Maximum traversal depth (1-10)")
    relationship_types: Optional[List[RelationshipType]] = Field(
        default=None, description="Filter by relationship types"
    )
    node_types: Optional[List[NodeType]] = Field(default=None, description="Filter by node types")

    # For find_path
    from_id: Optional[str] = Field(default=None, description="Source node ID for pathfinding")
    to_id: Optional[str] = Field(default=None, description="Target node ID for pathfinding")
    max_path_length: int = Field(default=5, description="Maximum path length (1-10)")

    # Common
    limit: int = Field(default=100, description="Maximum number of results")


class ExecuteScriptInput(BaseModel):
    """Input for executing a script node."""

    script_node_id: str = Field(description="Node ID of the script to execute")
    args: Optional[List[str]] = Field(default=None, description="Command-line arguments")
    env: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    timeout: int = Field(default=30, description="Execution timeout in seconds")
