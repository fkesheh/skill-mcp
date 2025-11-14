"""Query graph tool for traversal, pathfinding, and Cypher queries."""

import json
from typing import List

from mcp import types

from skill_mcp.core.config import GRAPH_ENABLED, GRAPH_MAX_TRAVERSAL_DEPTH
from skill_mcp.models_crud import QueryGraphInput
from skill_mcp.services.graph_service import GraphService, GraphServiceError


async def _handle_query(input_data: QueryGraphInput) -> List[types.TextContent]:
    """Handle raw Cypher query execution."""
    if not input_data.cypher_query:
        return [
            types.TextContent(type="text", text="❌ cypher_query is required for query operation")
        ]

    service = GraphService()
    try:
        results = await service.query_cypher(
            query=input_data.cypher_query,
            params=input_data.params,
        )

        if not results:
            return [types.TextContent(type="text", text="📋 Query returned no results")]

        output = f"📊 **Query Results** ({len(results)} rows)\n\n"
        output += "```json\n"
        output += json.dumps(results[: input_data.limit], indent=2)
        output += "\n```\n"

        if len(results) > input_data.limit:
            output += f"\n_Showing {input_data.limit} of {len(results)} results_"

        return [types.TextContent(type="text", text=output)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Query error: {str(e)}")]


async def _handle_traverse(input_data: QueryGraphInput) -> List[types.TextContent]:
    """Handle graph traversal from a starting node."""
    if not input_data.start_node_id:
        return [
            types.TextContent(
                type="text", text="❌ start_node_id is required for traverse operation"
            )
        ]

    # Validate max_depth
    max_depth = min(input_data.max_depth, GRAPH_MAX_TRAVERSAL_DEPTH)
    if max_depth != input_data.max_depth:
        warning = f"⚠️ max_depth capped at {GRAPH_MAX_TRAVERSAL_DEPTH}\n\n"
    else:
        warning = ""

    service = GraphService()
    try:
        result = await service.traverse_graph(
            start_node_id=input_data.start_node_id,
            direction=input_data.direction or "both",
            max_depth=max_depth,
            relationship_types=input_data.relationship_types,
            node_types=input_data.node_types,
            limit=input_data.limit,
        )

        nodes = result.get("nodes", [])
        relationships = result.get("relationships", [])

        if not nodes and not relationships:
            return [
                types.TextContent(
                    type="text",
                    text=f"📋 No connected nodes found for: `{input_data.start_node_id}`",
                )
            ]

        output = warning
        output += f"🌐 **Graph Traversal** from `{input_data.start_node_id}`\n\n"
        output += f"**Nodes found:** {len(nodes)}\n"
        output += f"**Relationships:** {len(relationships)}\n"
        output += f"**Max depth:** {max_depth}\n"
        output += f"**Direction:** {input_data.direction or 'both'}\n\n"

        if nodes:
            output += "**Nodes:**\n"
            for node in nodes[:20]:  # Show first 20 nodes
                output += f"• {node.get('name', 'Unknown')} (`{node.get('id', 'N/A')}`) - {node.get('type', 'Unknown')}\n"
            if len(nodes) > 20:
                output += f"... and {len(nodes) - 20} more\n"

        output += "\n```json\n"
        output += json.dumps({"nodes": nodes, "relationships": relationships}, indent=2)
        output += "\n```\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Traversal error: {str(e)}")]


async def _handle_find_path(input_data: QueryGraphInput) -> List[types.TextContent]:
    """Handle pathfinding between two nodes."""
    if not input_data.from_id:
        return [
            types.TextContent(type="text", text="❌ from_id is required for find_path operation")
        ]

    if not input_data.to_id:
        return [types.TextContent(type="text", text="❌ to_id is required for find_path operation")]

    service = GraphService()
    try:
        paths = await service.find_path(
            from_id=input_data.from_id,
            to_id=input_data.to_id,
            max_path_length=input_data.max_path_length,
        )

        if not paths:
            return [
                types.TextContent(
                    type="text",
                    text=f"📋 No path found between `{input_data.from_id}` and `{input_data.to_id}`",
                )
            ]

        output = f"🛤️ **{len(paths)} Path(s) Found**\n\n"
        output += f"**From:** `{input_data.from_id}`\n"
        output += f"**To:** `{input_data.to_id}`\n"
        output += f"**Max length:** {input_data.max_path_length}\n\n"

        for i, path in enumerate(paths, 1):
            nodes = path["nodes"]
            rels = path["relationships"]

            output += f"**Path {i}** ({len(nodes)} nodes, {len(rels)} hops):\n"
            for j, node in enumerate(nodes):
                output += f"  {j + 1}. {node['name']} (`{node['id']}`) - {node['type']}"
                if j < len(rels):
                    output += f" → **{rels[j]['type']}** →"
                output += "\n"
            output += "\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Pathfinding error: {str(e)}")]


async def _handle_stats(input_data: QueryGraphInput) -> List[types.TextContent]:
    """Handle graph statistics."""
    service = GraphService()
    try:
        stats = await service.get_graph_stats()

        output = "📊 **Graph Statistics**\n\n"
        output += f"**Total Nodes:** {stats['total_nodes']}\n"
        output += f"**Total Relationships:** {stats['total_relationships']}\n\n"

        if stats["node_counts"]:
            output += "**Node Counts:**\n"
            for node_type, count in sorted(stats["node_counts"].items(), key=lambda x: -x[1]):
                output += f"• {node_type}: {count}\n"
            output += "\n"

        if stats["relationship_counts"]:
            output += "**Relationship Counts:**\n"
            for rel_type, count in sorted(
                stats["relationship_counts"].items(), key=lambda x: -x[1]
            ):
                output += f"• {rel_type}: {count}\n"

        return [types.TextContent(type="text", text=output)]

    except GraphServiceError as e:
        return [types.TextContent(type="text", text=f"❌ Stats error: {str(e)}")]


class QueryGraph:
    """Query graph tool for MCP."""

    @staticmethod
    def get_tool_definition() -> List[types.Tool]:
        """Get tool definition for MCP registration."""
        return [
            types.Tool(
                name="query_graph",
                description="""Query and traverse the knowledge graph.

**Operations:**
- **query**: Execute raw Cypher query with optional parameters
- **traverse**: Walk the graph from a starting node with filters
- **find_path**: Find shortest paths between two nodes
- **stats**: Get graph statistics (node counts, relationship counts)

**Cypher Support:**
- Full Neo4j Cypher query language support
- Parameterized queries for safety
- Common patterns: MATCH, WHERE, RETURN, ORDER BY, LIMIT

See tool docstring for detailed examples and common Cypher patterns.""",
                inputSchema=QueryGraphInput.model_json_schema(),
            )
        ]

    def __init__(self):
        """Initialize query graph tool."""
        self.operation_map = {
            "query": _handle_query,
            "traverse": _handle_traverse,
            "find_path": _handle_find_path,
            "stats": _handle_stats,
        }

    async def handle(self, input_data: QueryGraphInput) -> List[types.TextContent]:
        """
        Handle query graph operations.

        Args:
            input_data: QueryGraphInput with operation and parameters

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
    async def query_graph(input_data: QueryGraphInput) -> List[types.TextContent]:
        """
        Query and traverse the knowledge graph.

        Operations:
        - query: Execute raw Cypher query
        - traverse: Walk the graph from a starting node
        - find_path: Find paths between two nodes
        - stats: Get graph statistics

        Examples:

        Execute a Cypher query:
        {
            "operation": "query",
            "cypher_query": "MATCH (n:Script) WHERE n.language = 'python' RETURN n.name, n.id LIMIT 10"
        }

        Query with parameters:
        {
            "operation": "query",
            "cypher_query": "MATCH (s:Skill {name: $name}) RETURN s",
            "params": {"name": "web-scraper"}
        }

        Traverse from a node:
        {
            "operation": "traverse",
            "start_node_id": "skill-abc123",
            "direction": "outgoing",
            "max_depth": 2,
            "relationship_types": ["CONTAINS", "DEPENDS_ON"],
            "node_types": ["Script"]
        }

        Find path between nodes:
        {
            "operation": "find_path",
            "from_id": "script-abc123",
            "to_id": "tool-def456",
            "max_path_length": 5
        }

        Get graph statistics:
        {
            "operation": "stats"
        }

        Common Cypher Queries:

        Find all Python scripts:
        MATCH (n:Script) WHERE n.language = 'python' RETURN n

        Find scripts that depend on a specific script:
        MATCH (s:Script)-[:DEPENDS_ON]->(target:Script {id: 'script-123'})
        RETURN s.name, s.id

        Find knowledge documents about a skill:
        MATCH (k:Knowledge)-[:EXPLAINS|REFERENCES]->(s:Skill {name: 'my-skill'})
        RETURN k.name, k.id, k.category

        Find all nodes connected to a skill:
        MATCH (s:Skill {name: 'my-skill'})-[r]-(connected)
        RETURN type(r) as relationship, labels(connected)[0] as node_type, connected.name

        Count nodes by type:
        MATCH (n)
        RETURN labels(n)[0] as type, count(n) as count
        ORDER BY count DESC
        """
        query = QueryGraph()
        return await query.handle(input_data)
