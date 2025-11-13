# Breaking Changes Analysis

## Impact Assessment: Current → New Architecture

### 1. Tool Name Changes

| Current Tool | New Tool(s) | Impact |
|--------------|-------------|--------|
| `graph_crud` | `node_crud`, `relationship_crud`, `query_graph` | **HIGH** - All existing clients must update |

### 2. Operation Changes

#### Current `graph_crud` Operations → New Mapping

| Old Operation | Old Tool | New Operation | New Tool | Breaking? |
|--------------|----------|---------------|----------|-----------|
| `sync` (skill) | graph_crud | `create` node + relationships | node_crud + relationship_crud | **YES** |
| `sync` (all) | graph_crud | Multiple `create` operations | node_crud | **YES** |
| `delete` | graph_crud | `delete` | node_crud | **MINOR** (same name, different params) |
| `stats` | graph_crud | `stats` | query_graph | **MINOR** (moved to different tool) |
| `query` (predefined) | graph_crud | `query` (Cypher) or `traverse` | query_graph | **YES** (different approach) |
| `analyze` | graph_crud | `traverse` or custom `query` | query_graph | **YES** |
| `visualize` | graph_crud | `traverse` + client-side viz | query_graph | **YES** |
| `search` | graph_crud | `list` with filters | node_crud | **MINOR** |

### 3. Input Parameter Changes

#### Example: Syncing a Skill

**OLD (graph_crud):**
```json
{
  "operation": "sync",
  "skill_name": "web-scraper",
  "sync_all": false
}
```

**NEW (node_crud + relationship_crud):**
```json
// Step 1: Create skill node
{
  "operation": "create",
  "node_type": "Skill",
  "name": "web-scraper",
  "description": "Web scraping utility",
  "tags": ["web", "scraping"],
  "properties": {
    "skill_path": "/home/user/.skill-mcp/skills/web-scraper",
    "has_env_file": true
  }
}

// Step 2: Create script nodes (for each .py file)
{
  "operation": "create",
  "node_type": "Script",
  "name": "scraper.py",
  "properties": {
    "language": "python",
    "file_path": "/home/user/.skill-mcp/skills/web-scraper/scraper.py",
    "is_executable": true
  }
}

// Step 3: Link skill to scripts
{
  "operation": "create",
  "from_id": "<skill-node-id>",
  "to_id": "<script-node-id>",
  "relationship_type": "CONTAINS"
}
```

**Migration Complexity: HIGH** - Multi-step operation vs single call

#### Example: Finding Related Skills

**OLD (graph_crud):**
```json
{
  "operation": "query",
  "query_type": "related_skills",
  "skill_name": "web-scraper",
  "depth": 2
}
```

**NEW (query_graph):**

Option A - Raw Cypher:
```json
{
  "operation": "query",
  "cypher_query": "MATCH (s:Skill {name: $name})-[*1..2]-(related:Skill) WHERE s <> related RETURN DISTINCT related.name, related.description",
  "params": {
    "name": "web-scraper"
  }
}
```

Option B - Traverse:
```json
{
  "operation": "traverse",
  "start_node_id": "<skill-node-id>",
  "direction": "both",
  "max_depth": 2,
  "node_types": ["Skill"]
}
```

**Migration Complexity: MEDIUM** - Requires Cypher knowledge or understanding traverse

### 4. Response Format Changes

#### Old Response (graph_crud query):
```json
{
  "results": [
    {"skill": "data-processor", "description": "...", "distance": 1},
    {"skill": "api-client", "description": "...", "distance": 2}
  ]
}
```

#### New Response (query_graph):
```json
{
  "nodes": [
    {
      "id": "node-123",
      "type": "Skill",
      "name": "data-processor",
      "description": "...",
      "properties": {...}
    },
    {
      "id": "node-456",
      "type": "Skill",
      "name": "api-client",
      "description": "...",
      "properties": {...}
    }
  ],
  "relationships": [
    {
      "from_id": "node-789",
      "to_id": "node-123",
      "type": "DEPENDS_ON"
    }
  ]
}
```

**Impact: MEDIUM** - Clients must parse different structure

### 5. Removed Operations

These convenience operations are REMOVED (replaced with generic queries):

| Removed Operation | Replacement |
|-------------------|-------------|
| `find_related_skills` | `traverse` or custom Cypher |
| `get_dependency_tree` | `traverse` with DEPENDS_ON filter |
| `find_circular_dependencies` | Custom Cypher query |
| `find_orphaned_skills` | Custom Cypher query |
| `get_skill_complexity_score` | Custom Cypher query with aggregation |
| `find_similar_skills` | Custom Cypher query (Jaccard similarity) |

**Impact: HIGH** - Users must learn Cypher or use traverse

### 6. Auto-Sync Behavior Change

**OLD:**
- Skills auto-synced to graph when created/updated via skill_crud
- Automatic file discovery and dependency analysis
- Background operation

**NEW:**
- Manual node creation required
- User explicitly creates Skill, Script, Knowledge nodes
- User explicitly creates relationships
- OR: Provide migration helper that does the sync

**Decision needed:** Keep auto-sync or make it explicit?

**Recommendation:** Keep auto-sync as optional feature via config flag

### 7. Python API Changes (if any)

**GraphService class:**

Old methods (deprecated):
```python
await graph_service.create_skill_node(skill_details)
await graph_service.create_file_node(skill_name, file_info)
await graph_service.link_skill_to_file(skill_name, file_path)
await graph_service.sync_skill_to_graph(skill_name)
```

New methods:
```python
await graph_service.create_node(node)
await graph_service.update_node(node_id, properties)
await graph_service.delete_node(node_id)
await graph_service.create_relationship(relationship)
await graph_service.query_cypher(query, params)
await graph_service.traverse_graph(start_id, direction, max_depth)
```

**Impact: HIGH for Python users** - Complete API change

---

## Migration Paths

### Path 1: Gradual Migration (Recommended)

**Timeline: 2 releases**

**Release 1 (v0.x.0):**
- Add new tools (node_crud, relationship_crud, query_graph)
- Keep old graph_crud with deprecation warnings
- Provide migration guide
- Auto-sync still works for backward compat

**Release 2 (v0.x+1.0):**
- Remove graph_crud
- Remove old GraphService methods
- All users migrated

**Pros:**
- Users have time to migrate
- Less risky
- Can test new architecture in parallel

**Cons:**
- Maintaining both systems temporarily
- Code complexity during transition

### Path 2: Hard Cutover

**Timeline: 1 release**

**Release 1 (v0.x.0):**
- Remove graph_crud immediately
- Add new tools
- Breaking change notice

**Pros:**
- Clean break
- Less code to maintain
- Faster completion

**Cons:**
- All users must update immediately
- Higher risk
- Potential user frustration

---

## Compatibility Matrix

| Feature | Old System | New System | Compatible? |
|---------|-----------|------------|-------------|
| Create skill | ✅ | ✅ | ❌ Different API |
| Query skills | ✅ | ✅ | ❌ Different approach |
| Delete skill | ✅ | ✅ | ⚠️ Similar but different params |
| Get stats | ✅ | ✅ | ⚠️ Moved to different tool |
| Execute script | ✅ | ✅ | ⚠️ Minor param changes |
| Auto-sync | ✅ | ❓ | TBD (config option?) |
| Predefined queries | ✅ | ❌ | ❌ Users must write Cypher |

---

## User Impact Analysis

### Persona: LLM Client (Claude, GPT, etc.)

**Impact: HIGH**
- Must learn new tool names
- Must understand node/relationship model
- Must learn basic Cypher OR use traverse API
- Benefit: More flexible, can create custom graphs

**Migration effort:** 2-4 hours to update prompts/examples

### Persona: Direct API User (Python/JavaScript)

**Impact: VERY HIGH**
- Must rewrite all graph interactions
- Must update imports
- Must handle different response formats

**Migration effort:** 4-8 hours depending on usage

### Persona: Casual User (via MCP)

**Impact: MEDIUM**
- Tool names change
- More steps for common operations
- Benefit: More control over graph structure

**Migration effort:** 1-2 hours reading docs

---

## Mitigation Strategies

### 1. Provide Migration Helpers

Create `tools/migration_helpers.py`:
```python
async def migrate_skill_to_nodes(skill_name: str):
    """Convert old skill sync to new node creation."""
    # Auto-creates Skill, Script, Knowledge nodes
    # Auto-creates relationships
    # Returns node IDs for reference
```

### 2. Cypher Query Library

Keep `graph_queries.py` as convenience library:
```python
# User can import and use
from skill_mcp.services.graph_queries import GraphQueries

query_dict = GraphQueries.find_related_skills("my-skill", depth=2)
result = await query_graph_tool(query_dict["query"], query_dict["params"])
```

### 3. Comprehensive Examples

Provide `docs/GRAPH_EXAMPLES.md` with:
- Common operations before/after
- Cypher query cookbook
- Traverse API examples

### 4. Deprecation Warnings

Add clear warnings to old tool:
```python
warnings.warn(
    "graph_crud is deprecated and will be removed in v0.x.0. "
    "Please migrate to node_crud, relationship_crud, query_graph. "
    "See docs/GRAPH_MIGRATION.md",
    DeprecationWarning
)
```

---

## Decision Points

### Decision 1: Migration Path
- ❓ **Option A:** Gradual migration (2 releases)
- ❓ **Option B:** Hard cutover (1 release)

**Recommendation:** Option A (gradual)

### Decision 2: Auto-Sync
- ❓ **Option A:** Keep auto-sync via config flag
- ❓ **Option B:** Remove auto-sync, manual only
- ❓ **Option C:** Provide sync helper function

**Recommendation:** Option A (keep as optional)

### Decision 3: Predefined Queries
- ❓ **Option A:** Keep graph_queries.py as helper library
- ❓ **Option B:** Remove, users write Cypher
- ❓ **Option C:** Provide query builder DSL

**Recommendation:** Option A (keep as helpers)

### Decision 4: Response Formats
- ❓ **Option A:** Generic node/relationship structure
- ❓ **Option B:** Maintain old response format compatibility
- ❓ **Option C:** Provide formatter functions

**Recommendation:** Option A (clean break)

---

## Rollback Plan

If new architecture has critical issues:

1. **Immediate:** Revert commits, redeploy old version
2. **Short-term:** Fix critical bugs in new architecture
3. **Long-term:** If unfixable, keep old system, abandon refactor

**Rollback triggers:**
- >50% increase in query latency
- Critical bugs affecting data integrity
- Overwhelming negative user feedback

---

## Next Steps

1. ✅ Review this breaking changes analysis
2. ❓ Get user approval on migration path (gradual vs hard cutover)
3. ❓ Get user approval on auto-sync decision
4. ❓ Get user approval on predefined queries decision
5. ▶️ Proceed to Phase 2: Design models
