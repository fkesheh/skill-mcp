# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**skill-mcp** is a Model Context Protocol (MCP) server that enables LLMs to manage skills stored in `~/.skill-mcp/skills`. The system uses a unified CRUD architecture to provide programmatic access to skill management, file operations, environment variables, and script execution.

## Architecture

### CRUD-Based Tool Design

The codebase recently underwent a major refactor to unify all operations into 3 main CRUD tools instead of 10+ individual tools:

1. **skill_crud** (`src/skill_mcp/tools/skill_crud.py`) - All skill operations (list, get, create, delete, validate)
2. **skill_files_crud** (`src/skill_mcp/tools/skill_files_crud.py`) - All file operations (read, create, update, delete) with bulk support
3. **skill_env_crud** (`src/skill_mcp/tools/skill_env_crud.py`) - All environment variable operations (read, set, delete, clear)
4. **run_skill_script** (`src/skill_mcp/tools/script_tools.py`) - Script execution only

**Key principle:** Tool descriptions should be clean and focused on functionality rather than implementation details. Avoid adding meta-commentary about "context window optimization" or comparing to old tools. AI talks with MCP through json, so examples need to be in json format.

### Layered Architecture

```
MCP Server (server.py)
    ↓
CRUD Tools (tools/*.py) - Operation routing
    ↓
Services (services/*.py) - Business logic
    ↓
Utils (utils/*.py) - Helpers & validation
```

**Services:**
- `skill_service.py` - Skill discovery, metadata parsing, validation
- `file_service.py` - File CRUD with path security validation
- `env_service.py` - Environment variable management with merge/replace modes
- `script_service.py` - Script execution with PEP 723 dependency detection

**Core modules:**
- `core/config.py` - All configuration constants (SKILLS_DIR, timeouts, limits)
- `core/exceptions.py` - Custom exception hierarchy
- `models.py` - Pydantic models for individual operations (backward compat)
- `models_crud.py` - Unified CRUD input models (SkillCrudInput, SkillFilesCrudInput, SkillEnvCrudInput)

### Critical Security Features

**Path validation** (`utils/path_utils.py`):
- All file paths validated to prevent directory traversal
- Rejects paths with "..", absolute paths, or paths escaping skill directory
- Used by all file operations

**Environment variable security**:
- Values never exposed when listing (only keys shown)
- Per-skill `.env` files instead of global secrets
- `EnvironmentService.set_variables()` always merges with existing variables

## Development Commands

### Running Tests
```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=src/skill_mcp --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_skill_crud.py -v

# Run single test
uv run pytest tests/test_skill_crud.py::test_skill_crud_list -v

# Run integration tests only
uv run pytest tests/integration/ -v
```

### Development Server
```bash
# Run server locally for testing
uv run -m skill_mcp.server

# Or use the entry point
uv run skill-mcp-server
```

### Dependency Management
```bash
# Sync dependencies (automatically creates .venv)
uv sync

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Code Quality
```bash
# Type checking (if mypy configured)
uv run mypy src/skill_mcp

# Format code
uv run ruff format src/

# Lint code
uv run ruff check src/
```

### Building & Publishing
```bash
# Build package
uv build

# Publish to PyPI (maintainers only)
uv publish
```

## Key Implementation Patterns

### 1. CRUD Operation Routing

All CRUD tools follow this pattern:
```python
async def tool_crud(input_data: CrudInput) -> list[types.TextContent]:
    operation = input_data.operation.lower()

    if operation == "create":
        return await _handle_create(input_data)
    elif operation == "read":
        return await _handle_read(input_data)
    # ... etc
```

### 2. Service Layer Separation

Services contain business logic, not MCP concerns:
```python
# GOOD - Service returns Python types
def get_skill_details(skill_name: str) -> SkillDetails:
    # ... logic ...
    return SkillDetails(...)

# GOOD - Tool wraps service and returns MCP types
async def _handle_get(input_data):
    details = SkillService.get_skill_details(input_data.skill_name)
    return [types.TextContent(type="text", text=str(details))]
```

### 3. Path Validation Pattern

Always validate paths before file operations:
```python
from skill_mcp.utils.path_utils import validate_relative_path

# Validate and get absolute path
abs_path = validate_relative_path(
    base_dir=SKILLS_DIR / skill_name,
    relative_path=file_path
)
```

### 4. Environment Variable Management

The `EnvironmentService.set_variables()` always merges with existing variables. To replace everything, use `clear_env()` first, then `set_variables()`.

### 5. PEP 723 Dependency Detection

Scripts with inline metadata are detected and run via `uv run`:
```python
# In script_service.py
if ScriptDetector.has_uv_metadata(script_path):
    cmd = ["uv", "run", str(script_path)]
else:
    cmd = [interpreter, str(script_path)]
```

## Common Patterns to Follow

### Adding a New Operation to Existing CRUD

1. Add operation to the input model in `models_crud.py`
2. Create `_handle_<operation>` method in the tool class
3. Add to the operation routing in `<tool>_crud()` method
4. Add service method if needed in appropriate service
5. Write tests in `tests/test_<tool>_crud.py`

### Adding a New Service Method

1. Add to appropriate service in `services/`
2. Use existing exceptions from `core/exceptions.py`
3. Validate paths using `path_utils.validate_relative_path()`
4. Return Python types, not MCP types
5. Add unit tests in `tests/`

### Tool Description Guidelines

When writing tool descriptions:
- Focus on what the tool does and how to use it
- Include clear examples with JSON input format
- Document all parameters and their purposes
- Explain operation modes where applicable
- **DO NOT** include implementation commentary like "context window optimization"
- **DO NOT** reference old tool names or migration notes

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures (tmp skills dir, sample skills)
├── test_skill_crud.py       # Skill CRUD operations
├── test_skill_files_crud.py # File CRUD operations
├── test_skill_env_crud.py   # Environment variable CRUD
├── test_*.py                # Service & utility tests
└── integration/
    └── test_mcp_server.py   # Full MCP server integration tests
```

**Key fixtures:**
- `tmp_skills_dir` - Temporary skills directory for testing
- `sample_skill` - Creates a sample skill with SKILL.md
- Mock configurations in conftest.py

## Configuration Constants

All configuration lives in `src/skill_mcp/core/config.py`:

```python
SKILLS_DIR = Path.home() / ".skill-mcp" / "skills"
MAX_FILE_SIZE = 1_000_000  # 1MB
MAX_OUTPUT_SIZE = 100_000  # 100KB
SCRIPT_TIMEOUT_SECONDS = 30
ENV_FILE_NAME = ".env"
SKILL_METADATA_FILE = "SKILL.md"
```

## Important Files

- `src/skill_mcp/server.py` - MCP server entry point, tool registration
- `src/skill_mcp/models_crud.py` - CRUD input models (modify when adding operations)
- `src/skill_mcp/services/env_service.py` - Recently enhanced with set_variables, delete_variables, clear_env
- `pyproject.toml` - Package metadata, entry point: `skill-mcp-server`

## Recent Major Changes

The codebase underwent a major refactor to unify tools:
- Replaced 10+ individual tools with 3 unified CRUD tools
- Removed old `skill_tools.py` and `file_tools.py`
- Added bulk operations for file create/update with atomic rollback
- Enhanced EnvironmentService with proper CRUD methods
- Simplified script_tools.py to focus only on execution

When adding features, maintain the CRUD pattern and avoid reverting to individual tool methods.
