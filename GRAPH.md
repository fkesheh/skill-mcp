# Neo4j Knowledge Graph for Skill-MCP

Transform skill-mcp into a **graph-powered knowledge management system** where skills, files, scripts, dependencies, and relationships form an interconnected knowledge graph.

## 🎯 Overview

The graph feature adds powerful discovery, dependency mapping, and impact analysis capabilities to skill-mcp by storing skill metadata and relationships in a Neo4j graph database.

### Key Benefits

- 🔍 **Discovery**: Find related skills through relationship traversal
- 📊 **Visualization**: Graph view of your skill ecosystem
- 🔗 **Dependency Mapping**: Complete dependency trees and conflict detection
- ⚡ **Impact Analysis**: See what breaks when you modify a skill
- 🎯 **Smart Recommendations**: Find similar skills and common patterns
- 📈 **Execution Tracking**: Monitor which scripts are used and how often

## 🏗️ Graph Schema

### Node Types

1. **Skill** - Represents a skill directory
   - Properties: `name`, `description`, `created_at`, `updated_at`, `has_env_file`, `file_count`, `script_count`

2. **File** - Any file in a skill
   - Labels: `:File:Python`, `:File:Markdown`, `:File:Shell`, `:File:Script`
   - Properties: `path`, `type`, `size`, `is_executable`, `modified_at`

3. **Dependency** - External package dependency
   - Properties: `package_name`, `version_spec`, `ecosystem` (python, npm)

4. **EnvVar** - Environment variable (key only, no values)
   - Properties: `key`, `skill_name`

5. **Module** - Import statement target
   - Labels: `:Module:StandardLib`, `:Module:ThirdParty`, `:Module:Local`
   - Properties: `name`, `type`

### Relationship Types

- `[:HAS_FILE]` - Skill → File
- `[:HAS_ENV_VAR]` - Skill → EnvVar
- `[:REFERENCES]` - Skill → Skill (cross-skill imports)
- `[:DEPENDS_ON]` - File → Dependency
- `[:IMPORTS]` - File → Module
- `[:EXECUTED]` - Skill → File (execution tracking)

## 📦 Setup

### 1. Install Neo4j

**Option A: Docker (Recommended)**

```bash
docker run \
    --name skill-mcp-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -v $HOME/.skill-mcp/neo4j/data:/data \
    -d \
    neo4j:latest
```

**Option B: Neo4j Desktop**

1. Download from [neo4j.com/download](https://neo4j.com/download/)
2. Create a new database
3. Note the connection details (bolt URI, username, password)

**Option C: Neo4j Aura (Cloud)**

1. Sign up at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/)
2. Create a free database
3. Note the connection string and credentials

### 2. Configure Environment

Add these environment variables:

```bash
export SKILL_MCP_GRAPH_ENABLED=true
export SKILL_MCP_GRAPH_AUTO_SYNC=true
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password
export NEO4J_DATABASE=neo4j
```

Or in your MCP client config:

```json
{
  "mcpServers": {
    "skill-mcp": {
      "command": "uvx",
      "args": ["--from", "skill-mcp", "skill-mcp-server"],
      "env": {
        "SKILL_MCP_GRAPH_ENABLED": "true",
        "SKILL_MCP_GRAPH_AUTO_SYNC": "true",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password"
      }
    }
  }
}
```

### 3. Initial Sync

After configuring, sync your existing skills to the graph:

```json
{
  "operation": "sync",
  "sync_all": true
}
```

## 🔧 Usage

### Sync Operations

**Sync all skills:**
```json
{
  "operation": "sync",
  "sync_all": true
}
```

**Sync single skill:**
```json
{
  "operation": "sync",
  "skill_name": "calculator"
}
```

**Delete skill from graph:**
```json
{
  "operation": "sync",
  "skill_name": "old-skill",
  "delete_skill": true
}
```

### Graph Statistics

```json
{
  "operation": "stats"
}
```

### Query Operations

**Find related skills:**
```json
{
  "operation": "query",
  "query_type": "related_skills",
  "skill_name": "calculator",
  "depth": 2
}
```

**Get dependency tree:**
```json
{
  "operation": "query",
  "query_type": "dependency_tree",
  "skill_name": "data-processor"
}
```

**Find skills using a package:**
```json
{
  "operation": "query",
  "query_type": "skills_using_package",
  "package_name": "requests"
}
```

**Detect circular dependencies:**
```json
{
  "operation": "query",
  "query_type": "circular_deps"
}
```

**Most used dependencies:**
```json
{
  "operation": "query",
  "query_type": "most_used_deps",
  "limit": 10
}
```

**Find orphaned skills:**
```json
{
  "operation": "query",
  "query_type": "orphaned_skills"
}
```

**Calculate skill complexity:**
```json
{
  "operation": "query",
  "query_type": "complexity",
  "skill_name": "calculator"
}
```

**Get import graph:**
```json
{
  "operation": "query",
  "query_type": "imports",
  "skill_name": "calculator"
}
```

**Find similar skills:**
```json
{
  "operation": "query",
  "query_type": "similar_skills",
  "skill_name": "calculator",
  "limit": 5
}
```

**Find dependency conflicts:**
```json
{
  "operation": "query",
  "query_type": "conflicts"
}
```

**Get execution history:**
```json
{
  "operation": "query",
  "query_type": "execution_history",
  "skill_name": "calculator",
  "limit": 10
}
```

**Custom Cypher query:**
```json
{
  "operation": "query",
  "cypher_query": "MATCH (s:Skill)-[:REFERENCES]->(s2:Skill) RETURN s.name, s2.name LIMIT 10"
}
```

### Impact Analysis

Analyze what would break if a skill is modified or deleted:

```json
{
  "operation": "analyze",
  "skill_name": "calculator"
}
```

Returns:
- Skills that depend on this skill
- Files that import from this skill
- Execution chains
- Impact score

### Visualization

**Export for Cytoscape.js:**
```json
{
  "operation": "visualize",
  "skill_name": "calculator",
  "format": "cytoscape"
}
```

**Get summary:**
```json
{
  "operation": "visualize",
  "skill_name": "calculator",
  "format": "summary"
}
```

**Raw JSON:**
```json
{
  "operation": "visualize",
  "skill_name": "calculator",
  "format": "json"
}
```

### Search

Search across skills:

```json
{
  "operation": "search",
  "search_query": "API client",
  "node_type": "Skill"
}
```

## 🔄 Auto-Sync Behavior

When `GRAPH_AUTO_SYNC=true`, the graph is automatically updated when:

1. **Skill created** - New skill nodes and structure synced
2. **Skill deleted** - Skill and related nodes removed
3. **File created/updated/deleted** - Skill re-synced to update graph
4. **Script executed** - Execution recorded with timestamp and success status

To disable auto-sync: `export SKILL_MCP_GRAPH_AUTO_SYNC=false`

## 🎨 Visualization Tools

### Using Cytoscape.js

1. Export graph data:
```json
{
  "operation": "visualize",
  "skill_name": "my-skill",
  "format": "cytoscape"
}
```

2. Use the JSON output in Cytoscape.js:
```javascript
cytoscape({
  container: document.getElementById('cy'),
  elements: <exported-data>,
  style: [
    {
      selector: 'node[type="Skill"]',
      style: {
        'background-color': '#4287f5',
        'label': 'data(label)'
      }
    }
  ]
});
```

### Using Neo4j Browser

1. Connect to Neo4j Browser: `http://localhost:7474`
2. Run Cypher queries directly:

```cypher
// Visualize skill and its files
MATCH (s:Skill {name: 'calculator'})-[:HAS_FILE]->(f:File)
RETURN s, f

// Show dependency graph
MATCH path = (s:Skill)-[:HAS_FILE]->(f:File)-[:DEPENDS_ON]->(d:Dependency)
WHERE s.name = 'calculator'
RETURN path

// Find skill relationships
MATCH path = (s1:Skill)-[:REFERENCES]->(s2:Skill)
RETURN path
LIMIT 50
```

## 🔒 Security

### Environment Variable Keys Only

`EnvVar` nodes store only the **key names**, never the values. This ensures sensitive data is never exposed in the graph.

### Cypher Injection Prevention

All queries use parameterized statements to prevent injection attacks.

### Access Control

- Neo4j authentication required
- Connection credentials in environment variables
- Optional feature - can be completely disabled

## 📊 Use Cases

### 1. Skill Discovery

**Scenario:** You need a skill for making HTTP requests but don't remember which one.

```json
{
  "operation": "search",
  "search_query": "HTTP request"
}
```

### 2. Dependency Consolidation

**Scenario:** Multiple skills use different versions of `requests`.

```json
{
  "operation": "query",
  "query_type": "conflicts"
}
```

Shows all version conflicts, allowing you to standardize.

### 3. Impact Analysis Before Changes

**Scenario:** You want to refactor a shared utility skill.

```json
{
  "operation": "analyze",
  "skill_name": "shared-utils"
}
```

See exactly which skills depend on it before making changes.

### 4. Finding Unused Skills

**Scenario:** Clean up your skills directory.

```json
{
  "operation": "query",
  "query_type": "orphaned_skills"
}
```

Find skills with no connections to others.

### 5. Execution Monitoring

**Scenario:** See which scripts are actually being used.

```json
{
  "operation": "query",
  "query_type": "execution_history",
  "skill_name": "data-processor",
  "limit": 20
}
```

## 🚀 Advanced Queries

### Find Skills Sharing Dependencies

```json
{
  "operation": "query",
  "cypher_query": "MATCH (s1:Skill)-[:HAS_FILE]->()-[:DEPENDS_ON]->(d:Dependency)<-[:DEPENDS_ON]-()<-[:HAS_FILE]-(s2:Skill) WHERE s1 <> s2 RETURN DISTINCT s1.name, s2.name, d.package_name LIMIT 20"
}
```

### Calculate Hub Skills

Skills with the most connections:

```json
{
  "operation": "query",
  "cypher_query": "MATCH (s:Skill) WITH s, size((s)-[:REFERENCES]-()) + size(()-[:REFERENCES]->(s)) as connections RETURN s.name, connections ORDER BY connections DESC LIMIT 10"
}
```

### Find Skill Clusters

```json
{
  "operation": "query",
  "cypher_query": "CALL gds.graph.project('skill-graph', 'Skill', 'REFERENCES') YIELD graphName"
}
```

(Requires Neo4j Graph Data Science plugin)

## ⚙️ Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SKILL_MCP_GRAPH_ENABLED` | `false` | Enable graph features |
| `SKILL_MCP_GRAPH_AUTO_SYNC` | `true` | Auto-sync changes to graph |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `NEO4J_DATABASE` | `neo4j` | Database name |
| `GRAPH_MAX_TRAVERSAL_DEPTH` | `5` | Max depth for relationship queries |
| `GRAPH_QUERY_TIMEOUT` | `30` | Query timeout in seconds |

## 🐛 Troubleshooting

### Cannot connect to Neo4j

**Error:** "Cannot connect to Neo4j database"

**Solutions:**
1. Check Neo4j is running: `docker ps` or Neo4j Desktop
2. Verify connection settings: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
3. Test connection: `cypher-shell -a bolt://localhost:7687 -u neo4j -p your_password`

### Graph out of sync

**Symptom:** Changes not reflected in graph queries

**Solution:** Re-sync all skills:
```json
{
  "operation": "sync",
  "sync_all": true
}
```

### Slow queries

**Solutions:**
1. Add indexes in Neo4j Browser:
```cypher
CREATE INDEX skill_name FOR (s:Skill) ON (s.name);
CREATE INDEX file_path FOR (f:File) ON (f.path);
CREATE INDEX dep_name FOR (d:Dependency) ON (d.package_name);
```

2. Reduce traversal depth:
```json
{
  "depth": 1
}
```

### Memory issues

For large skill collections, increase Neo4j memory:

```bash
docker run \
    -e NEO4J_dbms_memory_heap_max__size=2G \
    -e NEO4J_dbms_memory_pagecache_size=1G \
    neo4j:latest
```

## 🔮 Future Enhancements

Planned features for future releases:

- **Time-travel queries** - See skill state at any point in history
- **ML-powered recommendations** - Suggest skills based on usage patterns
- **GraphQL API** - Query graph via GraphQL
- **Real-time updates** - WebSocket-based live graph updates
- **Skill marketplace** - Discover and share skills via graph
- **Collaborative filtering** - "Users who used X also used Y"
- **Automated refactoring suggestions** - Based on graph analysis

## 📚 Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Cytoscape.js](https://js.cytoscape.org/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)
- [Model Context Protocol](https://modelcontextprotocol.io)

## 📄 License

Same as skill-mcp - MIT License
