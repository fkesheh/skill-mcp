"""Relationship CRUD tool for generic relationship operations."""

import json
from typing import List

from mcp import types

from skill_mcp.core.config import GRAPH_ENABLED
from skill_mcp.models import Relationship, RelationshipType
from skill_mcp.models_crud import RelationshipCrudInput
from skill_mcp.services.graph_service import GraphService, GraphServiceError


async def _handle_create(input_data: RelationshipCrudInput) -> List[types.TextContent]:
    """Handle relationship creation."""
    if not input_data.from_id:
        return [types.TextContent(type="text", text="❌ from_id is required for create operation")]

    if not input_data.to_id:
        return [types.TextContent(type="text", text="❌ to_id is required for create operation")]

    if not input_data.relationship_type:
        return [
            types.TextContent(
                type="text", text="❌ relationship_type is required for create operation"
            )
        ]

    # Create Relationship object
    relationship = Relationship(
        from_id=input_data.from_id,
        to_id=input_data.to_id,
        type=input_data.relationship_type,
        properties=input_data.properties or {},
    )

    service = GraphService()
    try:
        result = await service.create_relationship(relationship)

        output = f"✅ **Created {input_data.relationship_type.value} relationship**\n\n"
        output += f"**From:** `{input_data.from_id}`\n"
        output += f"**To:** `{input_data.to_id}`\n"
        if input_data.properties:
            output += (
                f"\n**Properties:**\n```json\n{json.dumps(input_data.properties, indent=2)}\n```\n"
            )

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error creating relationship: {str(e)}")]


async def _handle_get(input_data: RelationshipCrudInput) -> List[types.TextContent]:
    """Handle getting relationships for a node."""
    if not input_data.node_id:
        return [types.TextContent(type="text", text="❌ node_id is required for get operation")]

    service = GraphService()
    try:
        results = await service.get_relationships(
            node_id=input_data.node_id,
            direction=input_data.direction or "both",
            relationship_type=input_data.relationship_type,
        )

        if not results:
            return [
                types.TextContent(
                    type="text", text=f"📋 No relationships found for node: `{input_data.node_id}`"
                )
            ]

        dir_text = {"incoming": "incoming", "outgoing": "outgoing", "both": "all"}.get(
            input_data.direction or "both", "all"
        )

        output = f"📋 **{len(results)} {dir_text} relationships** for `{input_data.node_id}`\n\n"

        for rel in results:
            rel_type = rel["type"]
            other = rel["other_node"]
            output += f"• **{rel_type}**\n"
            output += f"  Connected to: {other['name']} (`{other['id']}`)\n"
            output += f"  Type: {other['type']}\n"

            # Show relationship properties if any
            props = rel.get("properties", {})
            excluded = {"created_at"}
            custom_props = {k: v for k, v in props.items() if k not in excluded}
            if custom_props:
                output += f"  Properties: {json.dumps(custom_props)}\n"
            output += "\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error getting relationships: {str(e)}")]


async def _handle_delete(input_data: RelationshipCrudInput) -> List[types.TextContent]:
    """Handle relationship deletion."""
    if not input_data.from_id:
        return [types.TextContent(type="text", text="❌ from_id is required for delete operation")]

    if not input_data.to_id:
        return [types.TextContent(type="text", text="❌ to_id is required for delete operation")]

    if not input_data.relationship_type:
        return [
            types.TextContent(
                type="text", text="❌ relationship_type is required for delete operation"
            )
        ]

    service = GraphService()
    try:
        await service.delete_relationship(
            from_id=input_data.from_id,
            to_id=input_data.to_id,
            relationship_type=input_data.relationship_type,
        )

        output = f"✅ **Deleted {input_data.relationship_type.value} relationship**\n\n"
        output += f"**From:** `{input_data.from_id}`\n"
        output += f"**To:** `{input_data.to_id}`"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error deleting relationship: {str(e)}")]


async def _handle_list(input_data: RelationshipCrudInput) -> List[types.TextContent]:
    """Handle listing all relationships."""
    service = GraphService()
    try:
        results = await service.list_relationships(
            filters=input_data.filters,
            limit=input_data.limit,
        )

        if not results:
            return [types.TextContent(type="text", text="📋 No relationships found")]

        output = f"📋 **{len(results)} Relationships**\n\n"

        for rel in results:
            from_node = rel["from_node"]
            to_node = rel["to_node"]
            rel_type = rel["type"]

            output += f"• **{rel_type}**\n"
            output += f"  {from_node['name']} (`{from_node['id']}`) → {to_node['name']} (`{to_node['id']}`)\n"
            output += f"  {from_node['type']} → {to_node['type']}\n\n"

        if len(results) == input_data.limit:
            output += f"_Showing {input_data.limit} relationships. Increase limit for more._"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Error listing relationships: {str(e)}")]


class RelationshipCrud:
    """Relationship CRUD tool for MCP."""

    @staticmethod
    def get_tool_definition() -> List[types.Tool]:
        """Get tool definition for MCP registration."""
        return [
            types.Tool(
                name="relationship_crud",
                description="""Generic CRUD operations for graph relationships.

**Operations:**
- **create**: Create a relationship between two nodes
- **get**: Get all relationships for a node
- **delete**: Delete a specific relationship
- **list**: List all relationships in the graph

**Relationship Types:**
- CONTAINS: Skill contains Scripts/Knowledge
- DEPENDS_ON: Script depends on another Script/Tool
- USES: Script uses Tool
- REFERENCES: Knowledge references Skill/Script
- RELATED_TO: Knowledge related to Knowledge
- EXPLAINS: Knowledge explains Skill
- IMPORTS: Script imports module/library

See tool docstring for detailed examples.""",
                inputSchema=RelationshipCrudInput.model_json_schema(),
            )
        ]

    def __init__(self):
        """Initialize relationship CRUD tool."""
        self.operation_map = {
            "create": _handle_create,
            "get": _handle_get,
            "delete": _handle_delete,
            "list": _handle_list,
        }

    async def handle(self, input_data: RelationshipCrudInput) -> List[types.TextContent]:
        """
        Handle relationship CRUD operations.

        Args:
            input_data: RelationshipCrudInput with operation and parameters

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
    async def relationship_crud(input_data: RelationshipCrudInput) -> List[types.TextContent]:
        """
        Generic CRUD operations for graph relationships.

        Operations:
        - create: Create a relationship between two nodes
        - get: Get all relationships for a node
        - delete: Delete a specific relationship
        - list: List all relationships in the graph

        Relationship Types:
        - CONTAINS: Skill contains Scripts/Knowledge
        - DEPENDS_ON: Script depends on another Script/Tool
        - USES: Script uses Tool
        - REFERENCES: Knowledge references Skill/Script
        - RELATED_TO: Knowledge related to Knowledge
        - EXPLAINS: Knowledge explains Skill
        - IMPORTS: Script imports module/library

        Examples:

        Create a CONTAINS relationship (Skill contains Script):
        {
            "operation": "create",
            "from_id": "skill-abc123",
            "to_id": "script-def456",
            "relationship_type": "CONTAINS"
        }

        Create a DEPENDS_ON relationship with properties:
        {
            "operation": "create",
            "from_id": "script-def456",
            "to_id": "script-ghi789",
            "relationship_type": "DEPENDS_ON",
            "properties": {
                "reason": "imports helper functions"
            }
        }

        Get all relationships for a node:
        {
            "operation": "get",
            "node_id": "skill-abc123",
            "direction": "outgoing"
        }

        Get specific relationship type:
        {
            "operation": "get",
            "node_id": "skill-abc123",
            "relationship_type": "CONTAINS",
            "direction": "outgoing"
        }

        Delete a relationship:
        {
            "operation": "delete",
            "from_id": "skill-abc123",
            "to_id": "script-def456",
            "relationship_type": "CONTAINS"
        }

        List all relationships:
        {
            "operation": "list",
            "limit": 50
        }
        """
        crud = RelationshipCrud()
        return await crud.handle(input_data)
