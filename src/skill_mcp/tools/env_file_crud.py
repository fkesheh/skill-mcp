"""EnvFile CRUD tool for managing environment file nodes."""

import json
from pathlib import Path
from typing import List
from uuid import uuid4

from mcp import types

from skill_mcp.core.config import GRAPH_ENABLED
from skill_mcp.models import Node, NodeType, Relationship, RelationshipType
from skill_mcp.models_crud import NodeCrudInput, RelationshipCrudInput
from skill_mcp.services.env_service import EnvironmentService
from skill_mcp.services.graph_service import GraphService, GraphServiceError


async def _handle_create(input_data: NodeCrudInput) -> List[types.TextContent]:
    """
    Handle EnvFile node creation.

    Creates an EnvFile node with a file path reference.
    IMPORTANT: Does NOT store env values in Neo4j, only the file path!
    """
    if not input_data.properties or "file_path" not in input_data.properties:
        return [
            types.TextContent(
                type="text",
                text="❌ file_path is required in properties for EnvFile nodes",
            )
        ]

    # Generate ID if not provided
    node_id = input_data.node_id or f"env-{uuid4().hex[:12]}"

    # Validate file path exists
    file_path = Path(input_data.properties["file_path"])
    if not file_path.exists():
        return [
            types.TextContent(
                type="text",
                text=f"❌ EnvFile not found at path: {file_path}",
            )
        ]

    node = Node(
        id=node_id,
        type=NodeType.ENVFILE,
        name=input_data.name,
        description=input_data.description or f"Environment file at {file_path}",
        tags=input_data.tags or [],
        properties={"file_path": str(file_path.absolute()), **input_data.properties},
    )

    service = GraphService()
    try:
        result = await service.create_node(node)

        output = f"✅ **Created EnvFile node**\n\n"
        output += f"**ID:** `{result['id']}`\n"
        output += f"**Name:** {result.get('name', 'N/A')}\n"
        output += f"**File Path:** {result.get('properties', {}).get('file_path', 'N/A')}\n"
        if result.get("description"):
            output += f"**Description:** {result['description']}\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error creating EnvFile node: {str(e)}")]


async def _handle_link(rel_data: dict) -> List[types.TextContent]:
    """
    Link an EnvFile to a Script or Skill node.

    Creates a USES_ENV relationship.
    """
    if not rel_data.get("from_id") or not rel_data.get("to_id"):
        return [
            types.TextContent(
                type="text",
                text="❌ Both from_id (Script/Skill) and to_id (EnvFile) are required",
            )
        ]

    relationship = Relationship(
        from_id=rel_data["from_id"],
        to_id=rel_data["to_id"],
        type=RelationshipType.USES_ENV,
        properties=rel_data.get("properties", {}),
    )

    service = GraphService()
    try:
        result = await service.create_relationship(relationship)

        output = f"✅ **Linked EnvFile to node**\n\n"
        output += f"**From:** `{rel_data['from_id']}` → **To:** `{rel_data['to_id']}`\n"
        output += f"**Relationship:** USES_ENV\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error linking EnvFile: {str(e)}")]


async def _handle_unlink(rel_data: dict) -> List[types.TextContent]:
    """
    Unlink an EnvFile from a Script or Skill node.

    Deletes the USES_ENV relationship.
    """
    if not rel_data.get("from_id") or not rel_data.get("to_id"):
        return [
            types.TextContent(
                type="text",
                text="❌ Both from_id (Script/Skill) and to_id (EnvFile) are required",
            )
        ]

    service = GraphService()
    try:
        await service.delete_relationship(
            rel_data["from_id"], rel_data["to_id"], RelationshipType.USES_ENV
        )

        output = f"✅ **Unlinked EnvFile**\n\n"
        output += f"Removed USES_ENV relationship between `{rel_data['from_id']}` and `{rel_data['to_id']}`\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error unlinking EnvFile: {str(e)}")]


async def _handle_get_for_node(node_id: str) -> List[types.TextContent]:
    """
    Get all EnvFile nodes linked to a specific Script or Skill.

    Returns EnvFile node info (NOT actual env values).
    """
    service = GraphService()
    try:
        # Query for all USES_ENV relationships
        query = """
        MATCH (node {id: $node_id})-[:USES_ENV]->(env:EnvFile)
        RETURN env
        """

        results = await service.query_cypher(query, {"node_id": node_id})

        if not results:
            return [
                types.TextContent(
                    type="text",
                    text=f"📋 No EnvFile nodes linked to `{node_id}`",
                )
            ]

        output = f"📋 **{len(results)} EnvFile(s) for `{node_id}`**\n\n"

        for result in results:
            env = result.get("env", {})
            output += f"• **{env.get('name', 'Unnamed')}** (`{env.get('id', 'N/A')}`)\n"
            output += f"  Path: {env.get('file_path', 'N/A')}\n"
            if env.get("description"):
                output += f"  Description: {env['description']}\n"
            output += "\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [
            types.TextContent(type="text", text=f"❌ Error getting EnvFiles for node: {str(e)}")
        ]


class EnvFileCrud:
    """EnvFile CRUD tool for MCP."""

    @staticmethod
    def get_tool_definition() -> List[types.Tool]:
        """Get tool definition for MCP registration."""
        return [
            types.Tool(
                name="env_file_crud",
                description="""Manage environment file references in the knowledge graph.

**SECURITY:** Only file paths are stored in Neo4j. Actual env values stay on disk!

**Operations:**
- **create**: Create EnvFile node with file path (requires file_path in properties)
- **read**: Get EnvFile node info by ID (shows path, NOT values)
- **update**: Update EnvFile metadata (name, description)
- **delete**: Delete EnvFile node
- **list**: List all EnvFile nodes
- **link**: Link EnvFile to Script/Skill (creates USES_ENV relationship)
- **unlink**: Unlink EnvFile from Script/Skill (removes USES_ENV relationship)
- **get_for_node**: Get all EnvFiles linked to a specific Script/Skill

**EnvFile Node Properties:**
- file_path (required): Absolute path to .env file on disk
- name: Descriptive name
- description: Optional description
- tags: Categorization tags

See tool docstring for detailed examples.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": [
                                "create",
                                "read",
                                "update",
                                "delete",
                                "list",
                                "link",
                                "unlink",
                                "get_for_node",
                            ],
                            "description": "Operation to perform",
                        },
                        "node_id": {
                            "type": "string",
                            "description": "EnvFile node ID (for read/update/delete/get_for_node)",
                        },
                        "name": {
                            "type": "string",
                            "description": "EnvFile name (for create/update)",
                        },
                        "description": {
                            "type": "string",
                            "description": "EnvFile description (for create/update)",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags for categorization",
                        },
                        "properties": {
                            "type": "object",
                            "description": "Node properties (must include file_path for create)",
                        },
                        "from_id": {
                            "type": "string",
                            "description": "Source node ID (Script/Skill) for link/unlink",
                        },
                        "to_id": {
                            "type": "string",
                            "description": "Target node ID (EnvFile) for link/unlink",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 50,
                            "description": "Max results for list operation",
                        },
                    },
                    "required": ["operation"],
                },
            )
        ]

    @staticmethod
    async def env_file_crud(input_data: dict) -> List[types.TextContent]:
        """
        Manage environment file references in the knowledge graph.

        SECURITY: Only file paths are stored in Neo4j. Actual env values stay on disk!

        Examples:

        Create EnvFile node:
        {
            "operation": "create",
            "name": "production-env",
            "description": "Production API keys",
            "properties": {
                "file_path": "/home/user/.skill-mcp/skills/web-scraper/.env"
            }
        }

        Link EnvFile to Script:
        {
            "operation": "link",
            "from_id": "script-abc123",
            "to_id": "env-def456"
        }

        Get EnvFiles for a Script:
        {
            "operation": "get_for_node",
            "node_id": "script-abc123"
        }

        List all EnvFiles:
        {
            "operation": "list"
        }

        Unlink EnvFile from Script:
        {
            "operation": "unlink",
            "from_id": "script-abc123",
            "to_id": "env-def456"
        }
        """
        if not GRAPH_ENABLED:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Graph feature is not enabled. Set GRAPH_ENABLED=true in config.",
                )
            ]

        operation = input_data.get("operation", "").lower()

        try:
            if operation == "create":
                # Convert dict to NodeCrudInput for create
                node_input = NodeCrudInput(
                    operation="create",
                    node_type=NodeType.ENVFILE,
                    node_id=input_data.get("node_id"),
                    name=input_data.get("name", ""),
                    description=input_data.get("description"),
                    tags=input_data.get("tags", []),
                    properties=input_data.get("properties", {}),
                )
                return await _handle_create(node_input)

            elif operation == "read":
                # Use node_crud for read
                from skill_mcp.tools.node_crud import NodeCrud

                node_input = NodeCrudInput(operation="read", node_id=input_data.get("node_id", ""))
                return await NodeCrud.node_crud(node_input)

            elif operation == "update":
                # Use node_crud for update
                from skill_mcp.tools.node_crud import NodeCrud

                node_input = NodeCrudInput(
                    operation="update",
                    node_id=input_data.get("node_id", ""),
                    name=input_data.get("name"),
                    description=input_data.get("description"),
                    tags=input_data.get("tags"),
                    properties=input_data.get("properties"),
                )
                return await NodeCrud.node_crud(node_input)

            elif operation == "delete":
                # Use node_crud for delete
                from skill_mcp.tools.node_crud import NodeCrud

                node_input = NodeCrudInput(
                    operation="delete", node_id=input_data.get("node_id", "")
                )
                return await NodeCrud.node_crud(node_input)

            elif operation == "list":
                # Use node_crud to list EnvFile nodes
                from skill_mcp.tools.node_crud import NodeCrud

                node_input = NodeCrudInput(
                    operation="list",
                    node_type=NodeType.ENVFILE,
                    limit=input_data.get("limit", 50),
                )
                return await NodeCrud.node_crud(node_input)

            elif operation == "link":
                return await _handle_link(input_data)

            elif operation == "unlink":
                return await _handle_unlink(input_data)

            elif operation == "get_for_node":
                if not input_data.get("node_id"):
                    return [
                        types.TextContent(
                            type="text",
                            text="❌ node_id is required for get_for_node operation",
                        )
                    ]
                return await _handle_get_for_node(input_data["node_id"])

            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Unknown operation: {operation}. Valid operations: create, read, update, delete, list, link, unlink, get_for_node",
                    )
                ]

        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]
