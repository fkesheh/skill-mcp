# Knowledge Management with Neo4j Graph

Extend your skill-mcp with **Knowledge** documents that work alongside your **Skills** in a unified knowledge graph.

## 🎯 Concept

- **Skills** = Executable code, scripts, automation
- **Knowledge** = Documentation, tutorials, guides, notes, articles
- **Graph** = Unified system connecting both with relationships

## 🏗️ Architecture

### Storage Structure

```
~/.skill-mcp/
├── skills/          # Executable skills (code)
│   ├── calculator/
│   ├── data-processor/
│   └── api-client/
└── knowledge/       # Knowledge documents (markdown)
    ├── how-to-use-calculator.md
    ├── api-design-principles.md
    └── python-best-practices.md
```

### Graph Schema

```
┌──────────┐         ┌───────────┐
│  Skill   │◄────────│ Knowledge │
│(code)    │ EXPLAINS│ (docs)    │
└──────────┘         └───────────┘
     │                     │
     │ HAS_FILE       RELATED_TO
     │                     │
     ▼                     ▼
┌──────────┐         ┌───────────┐
│   File   │         │ Knowledge │
└──────────┘         └───────────┘
     │
     │ DEPENDS_ON
     ▼
┌────────────┐
│ Dependency │
└────────────┘
```

### Node Types

**Knowledge Node:**
- `id` - Unique identifier
- `title` - Human-readable title
- `content` - Markdown content
- `category` - tutorial | guide | reference | note | article
- `tags` - Array of tags
- `author` - Author name
- `created_at`, `updated_at` - Timestamps

### Relationship Types

1. **Knowledge → Skill**
   - `[:EXPLAINS]` - Knowledge explains how to use skill
   - `[:REFERENCES]` - Knowledge mentions skill
   - `[:USES]` - Knowledge provides examples using skill

2. **Knowledge → Knowledge**
   - `[:RELATED_TO]` - Related knowledge documents

## 📝 Knowledge Operations

### Using the Graph Service Directly

```python
from skill_mcp.services.graph_service import GraphService
from skill_mcp.services.knowledge_service import KnowledgeService

# Create knowledge document
knowledge_service = KnowledgeService()
knowledge_service.create_knowledge(
    knowledge_id="calculator-tutorial",
    title="How to Use the Calculator Skill",
    content="# Calculator Tutorial\n\nThis guide explains...",
    category="tutorial",
    tags=["calculator", "math", "beginner"],
    author="Your Name"
)

# Sync to graph
graph_service = GraphService()
await graph_service.create_knowledge_node(
    knowledge_id="calculator-tutorial",
    title="How to Use the Calculator Skill",
    content="# Calculator Tutorial\n\nThis guide explains...",
    category="tutorial",
    tags=["calculator", "math", "beginner"],
    author="Your Name"
)

# Link knowledge to skill
await graph_service.link_knowledge_to_skill(
    knowledge_id="calculator-tutorial",
    skill_name="calculator",
    relationship_type="EXPLAINS"
)
```

### Via MCP Tool (Future - Not Yet Implemented)

The `skill_graph_crud` tool will be extended to support knowledge operations:

```json
{
  "operation": "knowledge",
  "knowledge_action": "create",
  "knowledge_id": "calculator-tutorial",
  "knowledge_title": "How to Use the Calculator Skill",
  "knowledge_content": "# Tutorial...",
  "knowledge_category": "tutorial",
  "knowledge_tags": ["calculator", "math"]
}

{
  "operation": "knowledge",
  "knowledge_action": "link_to_skill",
  "knowledge_id": "calculator-tutorial",
  "skill_name": "calculator",
  "relationship_type": "EXPLAINS"
}
```

## 🔍 Querying Knowledge

### List All Knowledge

```json
{
  "operation": "query",
  "query_type": "list_knowledge",
  "limit": 50
}
```

### Search Knowledge

```json
{
  "operation": "query",
  "query_type": "search_knowledge",
  "search_query": "tutorial",
  "limit": 20
}
```

### Find Knowledge About a Skill

```json
{
  "operation": "query",
  "query_type": "knowledge_about_skill",
  "skill_name": "calculator"
}
```

**Returns:** All tutorials, guides, and references that explain the calculator skill.

### Find Skills for Knowledge

```json
{
  "operation": "query",
  "query_type": "skills_for_knowledge",
  "knowledge_id": "python-best-practices"
}
```

**Returns:** All skills that are documented/referenced in this knowledge document.

### Get Knowledge by Category

```json
{
  "operation": "query",
  "query_type": "knowledge_by_category",
  "category_filter": "tutorial"
}
```

### Get Knowledge by Tag

```json
{
  "operation": "query",
  "query_type": "knowledge_by_tag",
  "tag_filter": "python"
}
```

### Find Related Knowledge

```json
{
  "operation": "query",
  "query_type": "related_knowledge",
  "knowledge_id": "calculator-tutorial",
  "limit": 10
}
```

### Visualize Knowledge Network

```json
{
  "operation": "query",
  "query_type": "knowledge_network",
  "limit": 50
}
```

**Returns:** Full network of knowledge documents and their relationships for visualization.

## 🎨 Use Cases

### 1. **Documentation Hub**

Create a knowledge base that documents all your skills:

```
knowledge/
├── tutorials/
│   ├── getting-started.md
│   ├── calculator-basics.md
│   └── advanced-data-processing.md
├── references/
│   ├── api-documentation.md
│   └── command-reference.md
└── guides/
    ├── best-practices.md
    └── troubleshooting.md
```

Link each document to relevant skills via `[:EXPLAINS]` relationships.

### 2. **Learning Paths**

Create tutorials that reference multiple skills:

```markdown
# Data Analysis Learning Path

This tutorial covers:
- Data collection (skill: web-scraper)
- Data cleaning (skill: data-processor)
- Visualization (skill: chart-maker)
```

Links: Knowledge → web-scraper, data-processor, chart-maker

### 3. **Architecture Documentation**

Document design decisions and link to implementing skills:

```markdown
# API Design Principles

Our API follows REST principles...
Implemented in: api-server skill
```

Link: Knowledge `[:REFERENCES]` → api-server skill

### 4. **Troubleshooting Guides**

Create guides that help debug issues:

```markdown
# Common Errors and Solutions

### Calculator Returns NaN
Check the calculator skill configuration...
```

Link: Knowledge `[:EXPLAINS]` → calculator skill

### 5. **Knowledge Networks**

Build interconnected documentation:

```
┌─────────────────┐         ┌──────────────────┐
│ Python Basics   │◄────────│ Advanced Python  │
│ (knowledge)     │RELATED_TO│ (knowledge)      │
└─────────────────┘         └──────────────────┘
         │                           │
    EXPLAINS                    EXPLAINS
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│ calculator      │         │ data-processor   │
│ (skill)         │         │ (skill)          │
└─────────────────┘         └──────────────────┘
```

## 📊 Advanced Queries

### Find Undocumented Skills

Skills without any knowledge documents:

```cypher
MATCH (s:Skill)
WHERE NOT (s)<-[:EXPLAINS|REFERENCES]-(:Knowledge)
RETURN s.name as undocumented_skill
```

### Most Referenced Skills

Skills with the most documentation:

```cypher
MATCH (k:Knowledge)-[:EXPLAINS|REFERENCES]->(s:Skill)
WITH s, count(k) as doc_count
RETURN s.name as skill, doc_count
ORDER BY doc_count DESC
LIMIT 10
```

### Knowledge Clusters

Find groups of related knowledge:

```cypher
MATCH (k1:Knowledge)-[:RELATED_TO*1..3]-(k2:Knowledge)
WHERE k1 <> k2
RETURN k1.id, collect(k2.id) as related_docs
```

### Skills and Their Documentation

Complete view of skills with their docs:

```cypher
MATCH (s:Skill)
OPTIONAL MATCH (k:Knowledge)-[:EXPLAINS]->(s)
RETURN s.name as skill,
       s.description,
       collect(k.title) as tutorials,
       count(k) as tutorial_count
ORDER BY tutorial_count DESC
```

## 🔄 Workflows

### Workflow 1: Document a New Skill

```bash
# 1. Create skill
skill_crud: create calculator skill

# 2. Create tutorial
knowledge_service.create_knowledge(
    id="calculator-guide",
    title="Calculator Skill Guide",
    content="...",
    category="tutorial"
)

# 3. Link to graph
graph_service.create_knowledge_node(...)
graph_service.link_knowledge_to_skill(
    "calculator-guide",
    "calculator",
    "EXPLAINS"
)

# 4. Query to verify
query_type: knowledge_about_skill, skill_name: calculator
```

### Workflow 2: Build Learning Path

```bash
# Create interconnected tutorials
1. Create "Python Basics" → link to calculator skill
2. Create "Advanced Python" → link to data-processor skill
3. Link "Advanced Python" RELATED_TO "Python Basics"

# Result: Learning progression
Python Basics → Advanced Python
     ↓               ↓
calculator    data-processor
```

### Workflow 3: Skill Discovery via Knowledge

```bash
# User searches: "How do I process CSV files?"

1. Search knowledge: query_type=search_knowledge, search="CSV"
2. Finds: "CSV Processing Guide" (knowledge)
3. Follow: skills_for_knowledge query
4. Discovers: data-processor, csv-parser skills
```

## 🚀 Getting Started

### 1. Enable Graph Feature

```bash
export SKILL_MCP_GRAPH_ENABLED=true
export NEO4J_URI=bolt://localhost:7687
# ... other config
```

### 2. Create Your First Knowledge Document

```python
from skill_mcp.services.knowledge_service import KnowledgeService

knowledge = KnowledgeService()
knowledge.create_knowledge(
    knowledge_id="welcome",
    title="Welcome to My Skills",
    content="# Welcome\n\nThis is my skill collection...",
    category="guide",
    tags=["introduction", "overview"]
)
```

### 3. Sync to Graph

```python
from skill_mcp.services.graph_service import GraphService

graph = GraphService()
await graph.create_knowledge_node(
    knowledge_id="welcome",
    title="Welcome to My Skills",
    content="...",
    category="guide",
    tags=["introduction", "overview"]
)
```

### 4. Link to Skills

```python
# Link welcome guide to your main skills
await graph.link_knowledge_to_skill("welcome", "calculator", "REFERENCES")
await graph.link_knowledge_to_skill("welcome", "data-processor", "REFERENCES")
```

### 5. Query and Explore

```json
{
  "operation": "query",
  "query_type": "knowledge_network",
  "limit": 100
}
```

## 🎯 Best Practices

### Knowledge Organization

1. **Use Categories Consistently**
   - `tutorial` - Step-by-step how-to guides
   - `guide` - Conceptual overviews
   - `reference` - API docs, command lists
   - `note` - Quick notes, snippets
   - `article` - In-depth explanations

2. **Tag Liberally**
   - Technology tags: `python`, `javascript`, `api`
   - Skill tags: `calculator`, `data-processing`
   - Level tags: `beginner`, `advanced`
   - Topic tags: `security`, `performance`

3. **Link Relationships Clearly**
   - `EXPLAINS` - Comprehensive documentation
   - `REFERENCES` - Brief mention
   - `USES` - Code examples using the skill

4. **Connect Related Knowledge**
   - Link prerequisites
   - Link follow-up guides
   - Link related topics

### Content Guidelines

- **Keep it Markdown** - Use standard markdown for portability
- **Include Examples** - Show code snippets
- **Link to Skills** - Reference actual skills by name
- **Update Regularly** - Keep knowledge in sync with skill changes
- **Use Frontmatter** - Store metadata at top of file

### Maintenance

```bash
# Periodically check for:

# 1. Undocumented skills
query_type: orphaned_skills

# 2. Outdated knowledge (manual review)
query_type: list_knowledge

# 3. Broken links (skills that no longer exist)
# Custom Cypher query to find knowledge → deleted skills
```

## 📚 Examples

See `/knowledge` directory for examples of:
- API documentation
- Tutorial series
- Best practices guides
- Troubleshooting docs
- Architecture decisions

## 🔮 Future Enhancements

- Auto-generate knowledge stubs from skills
- Knowledge versioning
- Collaborative editing
- Knowledge quality scoring
- Auto-linking via NLP
- Knowledge templates
- Export to static site
- Search with embeddings

## 📄 License

Same as skill-mcp - MIT License
