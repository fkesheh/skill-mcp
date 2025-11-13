"""Graph CRUD tool for Neo4j knowledge graph operations."""

import json
from typing import Any, Dict, List

from mcp import types

from skill_mcp.core.config import GRAPH_ENABLED, GRAPH_MAX_TRAVERSAL_DEPTH
from skill_mcp.core.exceptions import SkillMCPException
from skill_mcp.models_crud import GraphCrudInput
from skill_mcp.services.graph_queries import GraphQueries
from skill_mcp.services.graph_service import GraphService, GraphServiceError


class GraphCrud:
    """Unified CRUD tool for graph operations."""

    @staticmethod
    def get_tool_definition() -> List[types.Tool]:
        """Get graph CRUD tool definition."""
        return [
            types.Tool(
                name="skill_graph_crud",
                description="""
Unified tool for Neo4j knowledge graph operations on skills.

**IMPORTANT**: This feature is OPTIONAL and requires:
1. Neo4j database running (bolt://localhost:7687 by default)
2. Environment variable: SKILL_MCP_GRAPH_ENABLED=true
3. Neo4j credentials configured (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

If graph is not enabled, all operations will return appropriate messages.

## OPERATIONS

### 1. sync - Sync skills to graph database
Analyzes skills and creates/updates graph nodes and relationships.

Examples:
```json
{
  "operation": "sync",
  "skill_name": "calculator"
}

{
  "operation": "sync",
  "sync_all": true
}

{
  "operation": "sync",
  "skill_name": "old-skill",
  "delete_skill": true
}
```

### 2. stats - Get graph statistics
View counts of nodes and relationships in the graph.

Example:
```json
{
  "operation": "stats"
}
```

### 3. query - Query the knowledge graph
Execute predefined or custom queries.

**Predefined query types:**
- `related_skills` - Find skills related through imports/dependencies
- `dependency_tree` - Get complete dependency tree for a skill
- `skills_using_package` - Find all skills using a specific package
- `circular_deps` - Detect circular dependencies
- `most_used_deps` - Get most commonly used dependencies
- `orphaned_skills` - Find skills with no relationships
- `complexity` - Calculate complexity score for a skill
- `imports` - Get import graph for a skill
- `similar_skills` - Find skills with similar dependencies
- `conflicts` - Find dependency version conflicts
- `execution_history` - Get script execution history
- `neighborhood` - Get skill's immediate neighborhood

Examples:
```json
{
  "operation": "query",
  "query_type": "related_skills",
  "skill_name": "calculator",
  "depth": 2
}

{
  "operation": "query",
  "query_type": "dependency_tree",
  "skill_name": "data-processor"
}

{
  "operation": "query",
  "query_type": "skills_using_package",
  "package_name": "requests"
}

{
  "operation": "query",
  "query_type": "most_used_deps",
  "limit": 10
}

{
  "operation": "query",
  "cypher_query": "MATCH (s:Skill) RETURN s.name, s.description LIMIT 5"
}
```

### 4. analyze - Impact analysis
Analyze what would break if a skill is modified/deleted.

Example:
```json
{
  "operation": "analyze",
  "skill_name": "calculator"
}
```

### 5. visualize - Get graph visualization data
Export graph data in various formats for visualization tools.

Examples:
```json
{
  "operation": "visualize",
  "skill_name": "calculator",
  "format": "cytoscape"
}

{
  "operation": "visualize",
  "skill_name": "calculator",
  "format": "summary"
}
```

### 6. search - Full-text search
Search across graph nodes.

Example:
```json
{
  "operation": "search",
  "search_query": "API client",
  "node_type": "Skill"
}
```

## BENEFITS

🔍 **Discovery**: Find related skills through relationship traversal
📊 **Visualization**: Graph view of skill ecosystem
🔗 **Dependencies**: Complete dependency mapping
⚡ **Impact Analysis**: See what breaks when you change things
🎯 **Recommendations**: Suggest skills based on patterns

## SETUP

Docker (recommended):
```bash
docker run --name skill-mcp-neo4j \\
  -p 7474:7474 -p 7687:7687 \\
  -e NEO4J_AUTH=neo4j/your_password \\
  neo4j:latest
```

Configure in MCP client:
```json
{
  "mcpServers": {
    "skill-mcp": {
      "env": {
        "SKILL_MCP_GRAPH_ENABLED": "true",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

Then sync your skills:
```json
{"operation": "sync", "sync_all": true}
```
                """,
                inputSchema=GraphCrudInput.model_json_schema(),
            )
        ]

    @staticmethod
    async def skill_graph_crud(input_data: GraphCrudInput) -> List[types.TextContent]:
        """Handle graph CRUD operations."""
        # Check if graph is enabled
        if not GRAPH_ENABLED:
            return [
                types.TextContent(
                    type="text",
                    text="❌ Graph feature is not enabled.\n\n"
                    "To enable:\n"
                    "1. Install Neo4j (Docker: docker run --name neo4j -p 7474:7474 -p 7687:7687 "
                    "-e NEO4J_AUTH=neo4j/password neo4j:latest)\n"
                    "2. Set environment variable: SKILL_MCP_GRAPH_ENABLED=true\n"
                    "3. Configure Neo4j connection (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)\n"
                    "4. Restart MCP server\n",
                )
            ]

        operation = input_data.operation.lower()

        try:
            if operation == "sync":
                return await _handle_sync(input_data)
            elif operation == "stats":
                return await _handle_stats(input_data)
            elif operation == "query":
                return await _handle_query(input_data)
            elif operation == "analyze":
                return await _handle_analyze(input_data)
            elif operation == "visualize":
                return await _handle_visualize(input_data)
            elif operation == "search":
                return await _handle_search(input_data)
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Unknown operation: {operation}\n\n"
                        "Valid operations: sync, stats, query, analyze, visualize, search",
                    )
                ]

        except GraphServiceError as e:
            return [types.TextContent(type="text", text=f"❌ Graph Error: {str(e)}")]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]


# ===================
# Handler Functions
# ===================


async def _handle_sync(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle sync operations."""
    service = GraphService()

    # Check connection
    if not service.is_connected():
        return [
            types.TextContent(
                type="text",
                text="❌ Cannot connect to Neo4j database.\n\n"
                "Please check:\n"
                "1. Neo4j is running\n"
                "2. Connection settings are correct (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)\n"
                "3. Database is accessible\n",
            )
        ]

    # Delete skill from graph
    if input_data.delete_skill and input_data.skill_name:
        await service.delete_skill_from_graph(input_data.skill_name)
        return [
            types.TextContent(
                type="text",
                text=f"✅ Deleted skill '{input_data.skill_name}' from graph.",
            )
        ]

    # Sync all skills
    if input_data.sync_all:
        stats = await service.sync_all_skills_to_graph()
        output = "✅ **Synced all skills to graph**\n\n"
        output += f"**Statistics:**\n"
        output += f"- Total skills: {stats['total_skills']}\n"
        output += f"- Successfully synced: {stats['skills_synced']}\n"
        output += f"- Total files: {stats['total_files']}\n"
        output += f"- Total dependencies: {stats['total_dependencies']}\n"
        output += f"- Total imports: {stats['total_imports']}\n"

        if stats["errors"]:
            output += f"\n**Errors ({len(stats['errors'])}):**\n"
            for error in stats["errors"][:5]:  # Show first 5 errors
                output += f"- {error}\n"

        return [types.TextContent(type="text", text=output)]

    # Sync single skill
    if input_data.skill_name:
        stats = await service.sync_skill_to_graph(input_data.skill_name)
        output = f"✅ **Synced skill '{input_data.skill_name}' to graph**\n\n"
        output += f"**Statistics:**\n"
        output += f"- Files synced: {stats['files_synced']}\n"
        output += f"- Dependencies found: {stats['dependencies_found']}\n"
        output += f"- Imports found: {stats['imports_found']}\n"
        output += f"- Environment variables: {stats['env_vars_synced']}\n"

        return [types.TextContent(type="text", text=output)]

    return [
        types.TextContent(
            type="text",
            text="❌ Please specify either 'skill_name' or set 'sync_all' to true.",
        )
    ]


async def _handle_stats(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle stats operation."""
    service = GraphService()

    if not service.is_connected():
        return [types.TextContent(type="text", text="❌ Not connected to Neo4j database.")]

    stats = await service.get_graph_stats()

    output = "📊 **Graph Statistics**\n\n"
    output += f"**Nodes:** {stats['total_nodes']}\n"
    for node_type, count in stats["node_counts"].items():
        output += f"  - {node_type}: {count}\n"

    output += f"\n**Relationships:** {stats['total_relationships']}\n"
    for rel_type, count in stats["relationship_counts"].items():
        output += f"  - {rel_type}: {count}\n"

    return [types.TextContent(type="text", text=output)]


async def _handle_query(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle query operations."""
    service = GraphService()

    if not service.is_connected():
        return [types.TextContent(type="text", text="❌ Not connected to Neo4j database.")]

    # Custom Cypher query
    if input_data.cypher_query:
        results = await service.execute_query(input_data.cypher_query)
        output = f"**Query Results** ({len(results)} records)\n\n"
        output += json.dumps(results, indent=2, default=str)
        return [types.TextContent(type="text", text=output)]

    # Predefined queries
    if not input_data.query_type:
        return [
            types.TextContent(
                type="text",
                text="❌ Please specify either 'query_type' or 'cypher_query'.",
            )
        ]

    query_type = input_data.query_type.lower()

    # Get the appropriate query
    query_data: Dict[str, Any] = {}

    if query_type == "related_skills":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        depth = min(input_data.depth, GRAPH_MAX_TRAVERSAL_DEPTH)
        query_data = GraphQueries.find_related_skills(input_data.skill_name, depth)

    elif query_type == "dependency_tree":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        query_data = GraphQueries.get_dependency_tree(input_data.skill_name)

    elif query_type == "skills_using_package":
        if not input_data.package_name:
            return [types.TextContent(type="text", text="❌ 'package_name' is required.")]
        query_data = GraphQueries.find_skills_using_dependency(input_data.package_name)

    elif query_type == "circular_deps":
        query_data = GraphQueries.find_circular_dependencies()

    elif query_type == "most_used_deps":
        query_data = GraphQueries.get_most_used_dependencies(input_data.limit)

    elif query_type == "orphaned_skills":
        query_data = GraphQueries.find_orphaned_skills()

    elif query_type == "complexity":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        query_data = GraphQueries.get_skill_complexity_score(input_data.skill_name)

    elif query_type == "imports":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        query_data = GraphQueries.get_import_graph(input_data.skill_name)

    elif query_type == "similar_skills":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        query_data = GraphQueries.find_similar_skills(input_data.skill_name, input_data.limit)

    elif query_type == "conflicts":
        query_data = GraphQueries.get_dependency_conflicts()

    elif query_type == "execution_history":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        query_data = GraphQueries.get_execution_history(input_data.skill_name, input_data.limit)

    elif query_type == "neighborhood":
        if not input_data.skill_name:
            return [types.TextContent(type="text", text="❌ 'skill_name' is required.")]
        depth = min(input_data.depth, 3)
        query_data = GraphQueries.get_skill_neighborhood(input_data.skill_name, depth)

    else:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Unknown query type: {query_type}\n\n"
                "Valid types: related_skills, dependency_tree, skills_using_package, "
                "circular_deps, most_used_deps, orphaned_skills, complexity, imports, "
                "similar_skills, conflicts, execution_history, neighborhood",
            )
        ]

    # Execute the query
    results = await service.execute_query(query_data["query"], query_data["params"])

    # Format output
    output = f"**{query_type.replace('_', ' ').title()}**\n\n"
    output += f"Found {len(results)} result(s)\n\n"

    if results:
        output += json.dumps(results, indent=2, default=str)
    else:
        output += "No results found."

    return [types.TextContent(type="text", text=output)]


async def _handle_analyze(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle impact analysis."""
    service = GraphService()

    if not service.is_connected():
        return [types.TextContent(type="text", text="❌ Not connected to Neo4j database.")]

    if not input_data.skill_name:
        return [types.TextContent(type="text", text="❌ 'skill_name' is required for analysis.")]

    query_data = GraphQueries.get_skill_impact_analysis(input_data.skill_name)
    results = await service.execute_query(query_data["query"], query_data["params"])

    if not results:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Skill '{input_data.skill_name}' not found in graph. "
                "Please sync the skill first.",
            )
        ]

    result = results[0]
    output = f"🔍 **Impact Analysis: {input_data.skill_name}**\n\n"

    output += f"**Impact Score:** {result.get('impact_score', 0)}\n\n"

    referrers = result.get("referrers", [])
    if referrers:
        output += f"**⚠️ Skills that depend on this ({len(referrers)}):**\n"
        for ref in referrers:
            output += f"  - {ref.get('skill', 'Unknown')} (via {ref.get('via_file', 'unknown')})\n"
    else:
        output += "**✅ No skills depend on this skill**\n"

    files = result.get("files", [])
    if files:
        output += f"\n**Files in this skill ({len(files)}):**\n"
        for f in files[:10]:  # Show first 10
            output += f"  - {f}\n"
        if len(files) > 10:
            output += f"  ... and {len(files) - 10} more\n"

    dependencies = result.get("dependencies", [])
    if dependencies:
        output += f"\n**Dependencies ({len(dependencies)}):**\n"
        for dep in dependencies[:10]:
            output += f"  - {dep}\n"
        if len(dependencies) > 10:
            output += f"  ... and {len(dependencies) - 10} more\n"

    return [types.TextContent(type="text", text=output)]


async def _handle_visualize(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle visualization data export."""
    service = GraphService()

    if not service.is_connected():
        return [types.TextContent(type="text", text="❌ Not connected to Neo4j database.")]

    if not input_data.skill_name:
        return [
            types.TextContent(type="text", text="❌ 'skill_name' is required for visualization.")
        ]

    # Get neighborhood data
    depth = min(input_data.depth, 3)
    query_data = GraphQueries.get_skill_neighborhood(input_data.skill_name, depth)
    results = await service.execute_query(query_data["query"], query_data["params"])

    if not results or not results[0].get("nodes"):
        return [
            types.TextContent(
                type="text",
                text=f"❌ No graph data found for '{input_data.skill_name}'. "
                "Please sync the skill first.",
            )
        ]

    nodes = results[0]["nodes"]
    relationships = results[0]["relationships"]

    if input_data.format == "summary":
        output = f"📊 **Graph Visualization Summary: {input_data.skill_name}**\n\n"
        output += f"**Nodes:** {len(nodes)}\n"
        output += f"**Relationships:** {len(relationships)}\n\n"

        # Count by type
        node_types: Dict[str, int] = {}
        for node in nodes:
            labels = node.get("labels", [])
            if labels:
                label = labels[0]
                node_types[label] = node_types.get(label, 0) + 1

        output += "**Node Types:**\n"
        for node_type, count in sorted(node_types.items()):
            output += f"  - {node_type}: {count}\n"

        rel_types: Dict[str, int] = {}
        for rel in relationships:
            rel_type = rel.get("type", "Unknown")
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        output += "\n**Relationship Types:**\n"
        for rel_type, count in sorted(rel_types.items()):
            output += f"  - {rel_type}: {count}\n"

        return [types.TextContent(type="text", text=output)]

    elif input_data.format == "cytoscape":
        # Format for Cytoscape.js
        cytoscape_data = {
            "elements": {
                "nodes": [
                    {
                        "data": {
                            "id": str(node["id"]),
                            "label": node["properties"].get("name", "Unknown"),
                            "type": node["labels"][0] if node["labels"] else "Unknown",
                            **node["properties"],
                        }
                    }
                    for node in nodes
                ],
                "edges": [
                    {
                        "data": {
                            "id": f"{rel['source']}-{rel['target']}",
                            "source": str(rel["source"]),
                            "target": str(rel["target"]),
                            "label": rel["type"],
                            **rel.get("properties", {}),
                        }
                    }
                    for rel in relationships
                ],
            }
        }

        output = f"**Cytoscape.js format for '{input_data.skill_name}'**\n\n"
        output += json.dumps(cytoscape_data, indent=2, default=str)
        return [types.TextContent(type="text", text=output)]

    else:  # json
        viz_data = {"nodes": nodes, "relationships": relationships}
        output = f"**Graph data for '{input_data.skill_name}' (JSON format)**\n\n"
        output += json.dumps(viz_data, indent=2, default=str)
        return [types.TextContent(type="text", text=output)]


async def _handle_search(input_data: GraphCrudInput) -> List[types.TextContent]:
    """Handle full-text search."""
    service = GraphService()

    if not service.is_connected():
        return [types.TextContent(type="text", text="❌ Not connected to Neo4j database.")]

    if not input_data.search_query:
        return [types.TextContent(type="text", text="❌ 'search_query' is required for search.")]

    query_data = GraphQueries.find_skills_by_description(input_data.search_query)
    results = await service.execute_query(query_data["query"], query_data["params"])

    output = f"🔍 **Search Results for: \"{input_data.search_query}\"**\n\n"
    output += f"Found {len(results)} result(s)\n\n"

    if results:
        for result in results:
            output += f"**{result.get('skill', 'Unknown')}**\n"
            output += f"  Description: {result.get('description', 'No description')}\n"
            output += f"  Files: {result.get('file_count', 0)} | Scripts: {result.get('script_count', 0)}\n\n"
    else:
        output += "No results found."

    return [types.TextContent(type="text", text=output)]
