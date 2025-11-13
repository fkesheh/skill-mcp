# Graph Architecture Refactoring Plan

## Executive Summary

Refactoring graph system from specialized skill/knowledge operations to generic node-based architecture with 5 unified tools.

**Goal**: Replace complex, specialized graph_crud with simple, generic node/relationship/query operations.

---

## Current Architecture Analysis

### Current Files & Their Roles

#### Core Components
1. **`src/skill_mcp/services/graph_service.py`** (~650 lines)
   - Neo4j connection management
   - Specialized node creators: `create_skill_node()`, `create_file_node()`, `create_knowledge_node()`, etc.
   - Specialized relationship creators: `link_skill_to_file()`, `link_knowledge_to_skill()`, etc.
   - Complex syncing: `sync_skill_to_graph()`, `sync_all_skills_to_graph()`
   - **ACTION**: Refactor to generic `create_node()`, `create_relationship()`, `query_nodes()`

2. **`src/skill_mcp/services/graph_queries.py`** (~614 lines)
   - 30+ predefined Cypher query builders
   - Examples: `find_related_skills()`, `get_dependency_tree()`, `find_circular_dependencies()`
   - **ACTION**: Keep file but mark as deprecated convenience layer, or remove entirely

3. **`src/skill_mcp/tools/graph_crud.py`** (~627 lines)
   - MCP tool with complex routing: sync, stats, query, analyze, visualize, search
   - Handler functions: `_handle_sync()`, `_handle_stats()`, `_handle_query()`, etc.
   - 12+ query helper functions
   - **ACTION**: Replace with 3 new tools: node_crud, relationship_crud, query_graph

4. **`src/skill_mcp/utils/graph_utils.py`** (~73 lines)
   - Helper utilities: `get_current_timestamps()`, `require_connection` decorator
   - Auto-sync helpers: `auto_sync_skill_to_graph()`, `auto_delete_skill_from_graph()`
   - **ACTION**: Keep helper utilities, remove/update auto-sync functions

5. **`src/skill_mcp/services/knowledge_service.py`** (~180 lines)
   - File-based knowledge document management (YAML frontmatter + markdown)
   - **ACTION**: Keep as-is for now, knowledge nodes reference these files

6. **`src/skill_mcp/utils/ast_analyzer.py`** (~227 lines)
   - Python AST analysis for imports, function calls, env vars
   - **ACTION**: Keep as-is, used for analyzing Script nodes

#### Models
7. **`src/skill_mcp/models_crud.py`**
   - Contains `GraphCrudInput` with 20+ optional fields
   - **ACTION**: Replace with `NodeCrudInput`, `RelationshipCrudInput`, `QueryGraphInput`

8. **`src/skill_mcp/models.py`**
   - Contains `SkillDetails`, `FileInfo`, `ScriptInfo`
   - **ACTION**: Add new `Node`, `Relationship` models

#### Tests
9. **`tests/test_graph_*.py`** (6 files, 144 tests)
   - All tests cover current specialized architecture
   - **ACTION**: Refactor tests for generic operations, keep test count similar

---

## Target Architecture

### New Node Types

All nodes share common properties:
```python
class Node(BaseModel):
    id: str                    # Unique identifier
    type: NodeType             # "Skill" | "Knowledge" | "Script" | "Tool"
    name: str                  # Display name
    description: Optional[str] # Human-readable description
    tags: List[str]            # Categorization tags
    properties: Dict[str, Any] # Type-specific properties
    created_at: datetime
    updated_at: datetime
```

**Type-specific properties:**

**Skill nodes:**
- `skill_path: str` - Filesystem path to skill directory
- `has_env_file: bool` - Whether .env exists

**Knowledge nodes:**
- `category: str` - tutorial | guide | reference | note | article
- `author: Optional[str]` - Author name
- `content_path: str` - Path to .md file

**Script nodes:**
- `language: str` - python | javascript | shell
- `file_path: str` - Filesystem path to script
- `is_executable: bool` - Execute permission
- `has_pep723: bool` - For Python scripts with inline deps

**Tool nodes:**
- `mcp_server: str` - MCP server providing this tool
- `tool_name: str` - Tool identifier
- `input_schema: Dict` - MCP tool input schema

### Relationship Types

```python
class Relationship(BaseModel):
    from_id: str               # Source node ID
    to_id: str                 # Target node ID
    type: RelationshipType     # Relationship type
    properties: Dict[str, Any] # Relationship-specific data
    created_at: datetime
```

**Common relationship types:**
- `CONTAINS` - Skill contains Scripts/Knowledge
- `DEPENDS_ON` - Script depends on another Script/Tool
- `USES` - Script uses Tool
- `REFERENCES` - Knowledge references Skill/Script
- `RELATED_TO` - Knowledge related to Knowledge
- `EXPLAINS` - Knowledge explains Skill
- `IMPORTS` - Script imports module/library

---

## New Tool Specifications

### 1. `node_crud` Tool

**Input Model:**
```python
class NodeCrudInput(BaseModel):
    operation: Literal["create", "read", "update", "delete", "list"]

    # For create/update/delete/read
    node_id: Optional[str] = None
    node_type: Optional[NodeType] = None

    # For create/update
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    properties: Optional[Dict[str, Any]] = None

    # For list
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50
    offset: int = 0
```

**Operations:**
- `create` - Create new node
- `read` - Get node by ID
- `update` - Update node properties
- `delete` - Delete node
- `list` - List nodes with optional filters

### 2. `relationship_crud` Tool

**Input Model:**
```python
class RelationshipCrudInput(BaseModel):
    operation: Literal["create", "get", "delete", "list"]

    # For create/delete
    from_id: Optional[str] = None
    to_id: Optional[str] = None
    relationship_type: Optional[str] = None

    # For create
    properties: Optional[Dict[str, Any]] = None

    # For get
    node_id: Optional[str] = None
    direction: Optional[Literal["incoming", "outgoing", "both"]] = "both"

    # For list
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50
```

**Operations:**
- `create` - Create relationship between nodes
- `get` - Get all relationships for a node
- `delete` - Delete specific relationship
- `list` - List relationships with filters

### 3. `query_graph` Tool

**Input Model:**
```python
class QueryGraphInput(BaseModel):
    operation: Literal["query", "traverse", "find_path", "stats"]

    # For query (raw Cypher)
    cypher_query: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

    # For traverse
    start_node_id: Optional[str] = None
    direction: Optional[Literal["incoming", "outgoing", "both"]] = "both"
    max_depth: int = 3
    relationship_types: Optional[List[str]] = None
    node_types: Optional[List[NodeType]] = None

    # For find_path
    from_id: Optional[str] = None
    to_id: Optional[str] = None
    max_path_length: int = 5

    # Common
    limit: int = 100
```

**Operations:**
- `query` - Execute raw Cypher query
- `traverse` - Walk graph from starting node
- `find_path` - Find paths between two nodes
- `stats` - Get graph statistics

### 4. `execute_script` Tool (Update existing)

```python
class ExecuteScriptInput(BaseModel):
    script_node_id: str        # Node ID of script to execute
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30
```

### 5. `execute_python` Tool (New or update existing)

```python
class ExecutePythonInput(BaseModel):
    code: str                  # Python code to execute
    context: Optional[Dict[str, Any]] = None  # Variables to inject
    timeout: int = 10
```

---

## Migration Strategy

### Phase 1: Analysis ✅
- [x] Document current architecture
- [ ] Identify all breaking changes
- [ ] Create this detailed plan

### Phase 2: Design
- [ ] Create unified `Node` model in `models.py`
- [ ] Create `Relationship` model in `models.py`
- [ ] Create `NodeCrudInput` in `models_crud.py`
- [ ] Create `RelationshipCrudInput` in `models_crud.py`
- [ ] Create `QueryGraphInput` in `models_crud.py`

### Phase 3: Foundation (GraphService refactor)
- [ ] Add generic `create_node(node: Node) -> Dict` to GraphService
- [ ] Add generic `update_node(node_id, properties) -> Dict` to GraphService
- [ ] Add generic `delete_node(node_id) -> None` to GraphService
- [ ] Add generic `get_node(node_id) -> Node` to GraphService
- [ ] Add generic `list_nodes(filters, limit) -> List[Node]` to GraphService
- [ ] Add generic `create_relationship(rel: Relationship) -> Dict` to GraphService
- [ ] Add generic `get_relationships(node_id, direction, rel_type) -> List[Relationship]` to GraphService
- [ ] Add generic `delete_relationship(from_id, to_id, rel_type) -> None` to GraphService
- [ ] Add `query_cypher(query, params) -> List[Dict]` to GraphService
- [ ] Add `traverse_graph(start_id, direction, max_depth, filters) -> List[Dict]` to GraphService
- [ ] Add `find_path(from_id, to_id, max_length) -> List[List[Dict]]` to GraphService
- [ ] Keep old methods as deprecated wrappers (for backward compat)

### Phase 4: Tool Implementation
- [ ] Create `src/skill_mcp/tools/node_crud.py`
  - [ ] Implement `_handle_create()`
  - [ ] Implement `_handle_read()`
  - [ ] Implement `_handle_update()`
  - [ ] Implement `_handle_delete()`
  - [ ] Implement `_handle_list()`
  - [ ] Create `NodeCrud` class and register handlers
- [ ] Create `src/skill_mcp/tools/relationship_crud.py`
  - [ ] Implement `_handle_create()`
  - [ ] Implement `_handle_get()`
  - [ ] Implement `_handle_delete()`
  - [ ] Implement `_handle_list()`
  - [ ] Create `RelationshipCrud` class and register handlers
- [ ] Create `src/skill_mcp/tools/query_graph.py`
  - [ ] Implement `_handle_query()`
  - [ ] Implement `_handle_traverse()`
  - [ ] Implement `_handle_find_path()`
  - [ ] Implement `_handle_stats()`
  - [ ] Create `QueryGraph` class and register handlers
- [ ] Update `src/skill_mcp/tools/script_tools.py` to accept node_id parameter

### Phase 5: Testing
- [ ] Create `tests/test_node_models.py` - Test new Node/Relationship models
- [ ] Create `tests/test_node_crud.py` - Test node_crud tool (25+ tests)
- [ ] Create `tests/test_relationship_crud.py` - Test relationship_crud tool (20+ tests)
- [ ] Create `tests/test_query_graph.py` - Test query_graph tool (25+ tests)
- [ ] Update `tests/test_graph_service.py` - Test new generic methods (keep old test count)

### Phase 6: Migration & Deprecation
- [ ] Add deprecation warnings to `graph_crud.py`
- [ ] Update `src/skill_mcp/server.py` to register new tools:
  - [ ] Register `node_crud`
  - [ ] Register `relationship_crud`
  - [ ] Register `query_graph`
  - [ ] Keep `graph_crud` registered with deprecation notice
- [ ] Create migration helper script to convert existing graph data

### Phase 7: Cleanup (After validation)
- [ ] Remove `src/skill_mcp/tools/graph_crud.py`
- [ ] Mark `src/skill_mcp/services/graph_queries.py` as deprecated or remove
- [ ] Remove old specialized methods from GraphService
- [ ] Clean up unused imports

### Phase 8: Documentation
- [ ] Update `CLAUDE.md` with new architecture
- [ ] Create `docs/GRAPH_MIGRATION.md` user migration guide
- [ ] Add examples of common operations with new tools
- [ ] Update README if graph features mentioned

### Phase 9: Final Validation
- [ ] Run full test suite (ensure 150+ tests passing)
- [ ] Manual testing of all 5 tools
- [ ] Performance testing (ensure no regression)
- [ ] Commit refactored architecture
- [ ] Push to remote branch

---

## Breaking Changes

### For Users (MCP Clients)

**Old way:**
```json
{
  "operation": "sync",
  "skill_name": "my-skill"
}
```

**New way:**
```json
// Create skill node
{
  "operation": "create",
  "node_type": "Skill",
  "name": "my-skill",
  "properties": {
    "skill_path": "/path/to/skill",
    "has_env_file": true
  }
}

// Create script node
{
  "operation": "create",
  "node_type": "Script",
  "name": "main.py",
  "properties": {
    "language": "python",
    "file_path": "/path/to/skill/main.py"
  }
}

// Link skill to script
{
  "operation": "create",
  "from_id": "skill-node-id",
  "to_id": "script-node-id",
  "relationship_type": "CONTAINS"
}
```

### Backward Compatibility Strategy

**Option 1 (Recommended):** Keep old `graph_crud` for 1 release cycle
- Add deprecation warnings
- Provide migration guide
- Remove in next major version

**Option 2:** Hard cutover
- Remove immediately
- Users must update clients
- Faster cleanup

---

## File Change Summary

### Files to CREATE:
- `src/skill_mcp/tools/node_crud.py` (new)
- `src/skill_mcp/tools/relationship_crud.py` (new)
- `src/skill_mcp/tools/query_graph.py` (new)
- `tests/test_node_models.py` (new)
- `tests/test_node_crud.py` (new)
- `tests/test_relationship_crud.py` (new)
- `tests/test_query_graph.py` (new)
- `docs/GRAPH_MIGRATION.md` (new)

### Files to MODIFY:
- `src/skill_mcp/models.py` (add Node, Relationship)
- `src/skill_mcp/models_crud.py` (add 3 new input models)
- `src/skill_mcp/services/graph_service.py` (add generic methods)
- `src/skill_mcp/server.py` (register new tools)
- `tests/test_graph_service.py` (update for new methods)
- `CLAUDE.md` (document new architecture)

### Files to DEPRECATE/REMOVE (later):
- `src/skill_mcp/tools/graph_crud.py` (remove after migration)
- `src/skill_mcp/services/graph_queries.py` (optional remove)
- `tests/test_graph_crud.py` (remove after new tests work)
- `tests/test_graph_queries.py` (remove after new tests work)

### Files to KEEP AS-IS:
- `src/skill_mcp/services/knowledge_service.py`
- `src/skill_mcp/utils/ast_analyzer.py`
- `src/skill_mcp/utils/graph_utils.py` (minor updates)
- `tests/test_knowledge_service.py`
- `tests/test_ast_analyzer.py`
- `tests/test_graph_utils.py` (minor updates)

---

## Risk Mitigation

1. **Data Loss Risk**:
   - Keep old methods as deprecated wrappers
   - Provide data migration script
   - Test with sample data first

2. **Performance Risk**:
   - Generic operations might be slower than specialized
   - Mitigation: Benchmark before/after, optimize queries

3. **Compatibility Risk**:
   - Breaking changes for existing users
   - Mitigation: Keep old tool for 1 release cycle, provide migration guide

4. **Testing Gap Risk**:
   - New architecture needs comprehensive tests
   - Mitigation: Maintain ~150 test count, achieve similar coverage

---

## Success Criteria

- ✅ All 5 new tools implemented and working
- ✅ Test suite maintains 150+ tests with >85% coverage
- ✅ No performance regression (query time within 10% of current)
- ✅ Clean separation: nodes, relationships, queries
- ✅ GraphService reduced from ~650 lines to ~400 lines
- ✅ All existing tests pass with new architecture
- ✅ Documentation updated with examples

---

## Timeline Estimate

- Phase 1-2 (Analysis + Design): 1-2 hours
- Phase 3 (Foundation): 2-3 hours
- Phase 4 (Tools): 3-4 hours
- Phase 5 (Testing): 2-3 hours
- Phase 6-9 (Migration + Cleanup + Docs): 2-3 hours

**Total: 10-15 hours of development**

---

## Next Steps

1. Complete Phase 1 analysis ✅ (current step)
2. Get user approval on this plan
3. Begin Phase 2: Model design
4. Execute phases sequentially with testing at each step
