"""Node CRUD tool for generic node operations."""

import json
from typing import List
from uuid import uuid4

from mcp import types

from skill_mcp.core.config import GRAPH_ENABLED
from skill_mcp.models import Node, NodeType
from skill_mcp.models_crud import NodeCrudInput
from skill_mcp.services.graph_service import GraphService, GraphServiceError


async def _handle_create(input_data: NodeCrudInput) -> List[types.TextContent]:
    """Handle node creation."""
    if not input_data.node_type:
        return [
            types.TextContent(type="text", text="❌ node_type is required for create operation")
        ]

    if not input_data.name:
        return [types.TextContent(type="text", text="❌ name is required for create operation")]

    # Generate ID if not provided
    node_id = input_data.node_id or f"{input_data.node_type.value.lower()}-{uuid4().hex[:12]}"

    # Create Node object
    node = Node(
        id=node_id,
        type=input_data.node_type,
        name=input_data.name,
        description=input_data.description or "",
        tags=input_data.tags or [],
        properties=input_data.properties or {},
    )

    service = GraphService()
    try:
        result = await service.create_node(node)

        output = f"✅ **Created {input_data.node_type.value} node**\n\n"
        output += f"**ID:** `{result.get('id', node_id)}`\n"
        output += f"**Name:** {result.get('name', input_data.name)}\n"
        if result.get("description"):
            output += f"**Description:** {result['description']}\n"
        if result.get("tags"):
            output += f"**Tags:** {', '.join(result['tags'])}\n"
        if input_data.properties:
            output += (
                f"\n**Properties:**\n```json\n{json.dumps(input_data.properties, indent=2)}\n```\n"
            )

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error creating node: {str(e)}")]


async def _handle_read(input_data: NodeCrudInput) -> List[types.TextContent]:
    """Handle node read."""
    if not input_data.node_id:
        return [types.TextContent(type="text", text="❌ node_id is required for read operation")]

    service = GraphService()
    try:
        result = await service.get_node(input_data.node_id)

        if not result:
            return [types.TextContent(type="text", text=f"❌ Node not found: {input_data.node_id}")]

        output = f"📄 **Node Details**\n\n"
        output += f"**ID:** `{result['id']}`\n"
        output += f"**Type:** {result['type']}\n"
        output += f"**Name:** {result['name']}\n"
        if result.get("description"):
            output += f"**Description:** {result['description']}\n"
        if result.get("tags"):
            output += f"**Tags:** {', '.join(result['tags'])}\n"
        if result.get("created_at"):
            output += f"**Created:** {result['created_at']}\n"
        if result.get("updated_at"):
            output += f"**Updated:** {result['updated_at']}\n"

        # Show custom properties
        excluded_keys = {"id", "name", "description", "tags", "created_at", "updated_at"}
        custom_props = {k: v for k, v in result.items() if k not in excluded_keys}
        if custom_props:
            output += f"\n**Properties:**\n```json\n{json.dumps(custom_props, indent=2)}\n```\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error reading node: {str(e)}")]


async def _handle_update(input_data: NodeCrudInput) -> List[types.TextContent]:
    """Handle node update."""
    if not input_data.node_id:
        return [types.TextContent(type="text", text="❌ node_id is required for update operation")]

    # Build properties to update
    update_props = input_data.properties or {}
    if input_data.name:
        update_props["name"] = input_data.name
    if input_data.description is not None:
        update_props["description"] = input_data.description
    if input_data.tags is not None:
        update_props["tags"] = input_data.tags

    if not update_props:
        return [types.TextContent(type="text", text="❌ No properties provided to update")]

    service = GraphService()
    try:
        result = await service.update_node(input_data.node_id, update_props)

        if not result:
            return [types.TextContent(type="text", text=f"❌ Node not found: {input_data.node_id}")]

        output = f"✅ **Updated node:** `{input_data.node_id}`\n\n"
        output += f"**Updated properties:**\n```json\n{json.dumps(update_props, indent=2)}\n```\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error updating node: {str(e)}")]


async def _handle_delete(input_data: NodeCrudInput) -> List[types.TextContent]:
    """Handle node deletion."""
    if not input_data.node_id:
        return [types.TextContent(type="text", text="❌ node_id is required for delete operation")]

    service = GraphService()
    try:
        await service.delete_node(input_data.node_id)

        output = f"✅ **Deleted node:** `{input_data.node_id}`\n\n"
        output += "All relationships to/from this node were also deleted."

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error deleting node: {str(e)}")]


async def _handle_list(input_data: NodeCrudInput) -> List[types.TextContent]:
    """Handle node listing."""
    service = GraphService()
    try:
        results = await service.list_nodes(
            node_type=input_data.node_type,
            filters=input_data.filters,
            limit=input_data.limit,
            offset=input_data.offset,
        )

        if not results:
            filter_desc = f" ({input_data.node_type.value})" if input_data.node_type else ""
            return [types.TextContent(type="text", text=f"📋 No nodes found{filter_desc}")]

        type_filter = f" {input_data.node_type.value}" if input_data.node_type else ""
        output = f"📋 **{len(results)}{type_filter} Nodes**"
        if input_data.offset > 0:
            output += f" (offset: {input_data.offset})"
        output += "\n\n"

        for node in results:
            output += f"• **{node['name']}** (`{node['id']}`)\n"
            output += f"  Type: {node['type']}"
            if node.get("description"):
                output += f" | {node['description'][:60]}..."
            if node.get("tags"):
                output += f"\n  Tags: {', '.join(node['tags'][:3])}"
            output += "\n\n"

        if len(results) == input_data.limit:
            output += f"_Showing {input_data.limit} nodes. Use offset parameter for more._"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error listing nodes: {str(e)}")]


class NodeCrud:
    """Node CRUD tool for MCP."""

    @staticmethod
    def get_tool_definition() -> List[types.Tool]:
        """Get tool definition for MCP registration."""
        return [
            types.Tool(
                name="node_crud",
                description="""Generic CRUD operations for graph nodes.

**Operations:**
- **create**: Create a new node (requires: node_type, name)
- **read**: Get node by ID (requires: node_id)
- **update**: Update node properties (requires: node_id, properties)
- **delete**: Delete node and relationships (requires: node_id)
- **list**: List nodes with optional filters

**Valid Node Types:**
- **Skill**: Represents a skill directory with scripts/docs
- **Knowledge**: Represents a knowledge document (.md file)
- **Script**: Represents an executable script (.py, .js, .sh, etc.)
- **Tool**: Represents an MCP tool/function definition
- **EnvFile**: Represents an environment file reference (.env file path)

**Note:** Use the exact string values above (case-sensitive) when specifying node_type.

See tool docstring for detailed examples.""",
                inputSchema=NodeCrudInput.model_json_schema(),
            )
        ]

    def __init__(self):
        """Initialize node CRUD tool."""
        self.operation_map = {
            "create": _handle_create,
            "read": _handle_read,
            "update": _handle_update,
            "delete": _handle_delete,
            "list": _handle_list,
        }

    async def handle(self, input_data: NodeCrudInput) -> List[types.TextContent]:
        """
        Handle node CRUD operations.

        Args:
            input_data: NodeCrudInput with operation and parameters

        Returns:
            List of TextContent responses
        """
        if not GRAPH_ENABLED:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Graph feature is not enabled. Set GRAPH_ENABLED=true in config.",
                )
            ]

        operation = input_data.operation.lower()

        if operation not in self.operation_map:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Unknown operation: {operation}. Valid operations: {', '.join(self.operation_map.keys())}",
                )
            ]

        handler = self.operation_map[operation]
        return await handler(input_data)

    @staticmethod
    async def node_crud(input_data: NodeCrudInput) -> List[types.TextContent]:
        """
        Generic CRUD operations for graph nodes.

        Operations:
        - create: Create a new node (requires: node_type, name)
        - read: Get node by ID (requires: node_id)
        - update: Update node properties (requires: node_id, properties)
        - delete: Delete node and relationships (requires: node_id)
        - list: List nodes with optional filters

        Valid Node Types (case-sensitive):
        - Skill: Represents a skill directory with scripts/docs
        - Knowledge: Represents a knowledge document (.md file)
        - Script: Represents an executable script (.py, .js, .sh, etc.)
        - Tool: Represents an MCP tool/function definition
        - EnvFile: Represents an environment file reference (.env file path)

        Examples:

        Create a Skill node:
        {
            "operation": "create",
            "node_type": "Skill",
            "name": "web-scraper",
            "description": "Web scraping utility",
            "tags": ["web", "scraping"],
            "properties": {
                "skill_path": "/path/to/skill",
                "has_env_file": true
            }
        }

        Create a Script node:
        {
            "operation": "create",
            "node_type": "Script",
            "name": "scraper.py",
            "description": "Main scraper script",
            "properties": {
                "language": "python",
                "file_path": "/path/to/scraper.py",
                "is_executable": true
            }
        }

        Read a node:
        {
            "operation": "read",
            "node_id": "skill-abc123"
        }

        Update a node:
        {
            "operation": "update",
            "node_id": "skill-abc123",
            "properties": {
                "description": "Updated description"
            }
        }

        List all nodes of a type:
        {
            "operation": "list",
            "node_type": "Script",
            "limit": 20
        }

        Delete a node:
        {
            "operation": "delete",
            "node_id": "skill-abc123"
        }
        """
        crud = NodeCrud()
        return await crud.handle(input_data)
