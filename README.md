# Skill Management MCP Server

A Model Context Protocol (MCP) server that enables Claude to manage skills stored in `~/.skill-mcp/skills`. This system allows Claude to create, edit, run, and manage skills programmatically, including execution of skill scripts with environment variables.

## Quick Status

**Status:** ✅ Production Ready
**Test Coverage:** 86% (145/145 tests passing)
**Deployed:** October 18, 2025
**Architecture:** 22-module modular Python package with unified CRUD architecture

## Overview

**TL;DR:** Write Python code that unifies multiple skills in one execution - follows [Anthropic's MCP pattern](https://www.anthropic.com/engineering/code-execution-with-mcp) for 98.7% more efficient agents.

This project consists of two main components:

1. **MCP Server** (`src/skill_mcp/server.py`) - A Python package providing 5 unified CRUD tools for skill management
2. **Skills Directory** (`~/.skill-mcp/skills/`) - Where you store and manage your skills

## Key Advantages

### 🚀 Unified Multi-Skill Execution (Code Execution with MCP)

**Build once, compose everywhere** - Execute Python code that seamlessly combines multiple skills in a single run:

```python
# One execution, multiple skills unified!
# Imports from calculator, data-processor, and weather skills
from math_utils import calculate_average          # calculator skill
from json_fetcher import fetch_json                # data-processor skill
from weather_api import get_forecast               # weather skill

# Fetch weather data
weather = fetch_json('https://api.weather.com/cities')

# Calculate averages using calculator utilities
temps = [city['temp'] for city in weather['cities']]
avg_temp = calculate_average(temps)

# Get detailed forecast
forecast = get_forecast('London')
print(f"Average temperature: {avg_temp}°F")
print(f"London forecast: {forecast}")
```

**What makes this powerful:**
- ✅ **Context-efficient** - Dependencies and env vars auto-aggregated from all referenced skills
- ✅ **Composable** - Mix and match utilities from any skill like building blocks
- ✅ **No redundancy** - Declare PEP 723 dependencies once in library skills, reuse everywhere
- ✅ **Progressive disclosure** - Load only the skills you need, when you need them
- ✅ **Follows Anthropic's MCP pattern** - [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) for efficient agents

**Efficiency gains:**
- 📉 **98.7% fewer tokens** when discovering tools progressively vs loading all upfront
- 🔄 **Intermediate results stay in code** - Process large datasets without bloating context
- ⚡ **Single execution** - Complex multi-step workflows in one code block instead of chained tool calls

This aligns with Anthropic's research showing agents scale better by writing code to call tools rather than making direct tool calls for each operation.

### 🔓 Not Locked to Claude UI

Unlike the Claude interface, this system uses the **Model Context Protocol (MCP)**, which is:

- ✅ **Universal** - Works with Claude Desktop, claude.ai, Cursor, and any MCP-compatible client
- ✅ **Not tied to Claude** - Same skills work everywhere MCP is supported
- ✅ **Future-proof** - Not dependent on Claude's ecosystem or policy changes
- ✅ **Local-first** - Full control over your skills and data

### 🎯 Use Skills Everywhere

Your skills can run in:
- **Cursor** - IDE integration with MCP support
- **Claude Desktop** - Native app with MCP access
- **claude.ai** - Web interface with MCP support
- **Any MCP client** - Growing ecosystem of compatible applications

### 📦 Independent & Modular

- ✅ Each skill is self-contained with its own files, scripts, and environment
- ✅ No dependency on proprietary Claude features
- ✅ Can be versioned, shared, and reused across projects
- ✅ Standard MCP protocol ensures compatibility

### 🔄 Share Skills Across All MCP Clients

- ✅ **One skill directory, multiple clients** - Create once, use everywhere
- ✅ **Same skills in Cursor and Claude** - No duplication needed
- ✅ **Seamless switching** - Move between tools without reconfiguring
- ✅ **Consistent experience** - Skills work identically across all MCP clients
- ✅ **Centralized management** - Update skills in one place, available everywhere

### 🤖 LLM-Managed Skills (No Manual Copy-Paste)

Instead of manually copying, zipping, and uploading files:

```
❌ OLD WAY: Manual process
   1. Create skill files locally
   2. Zip the skill folder
   3. Upload to Claude interface
   4. Wait for processing
   5. Can't easily modify or version

✅ NEW WAY: LLM-managed programmatically
   1. Tell Claude: "Create a new skill called 'data-processor'"
   2. Claude creates the skill directory and SKILL.md
   3. Tell Claude: "Add a Python script to process CSVs"
   4. Claude creates and tests the script
   5. Tell Claude: "Set the API key for this skill"
   6. Claude updates the .env file
   7. Tell Claude: "Run the script with this data"
   8. Claude executes it and shows results - all instantly!
```

**Key Benefits:**
- ✅ **No manual file operations** - LLM handles creation, editing, deletion
- ✅ **Instant changes** - No upload/download/reload cycles
- ✅ **Full version control** - Skills are regular files, can use git
- ✅ **Easy modification** - LLM can edit scripts on the fly
- ✅ **Testable** - LLM can create and run scripts immediately
- ✅ **Collaborative** - Teams can develop skills together via MCP

## Features

### Skill Management
- ✅ List all available skills
- ✅ Browse skill files and directory structure
- ✅ Read skill files (SKILL.md, scripts, references, assets)
- ✅ Create new skill files and directories
- ✅ Update existing skill files
- ✅ Delete skill files

### Script Execution
- ✅ Run Python, Bash, and other executable scripts
- ✅ **Automatic dependency management** for Python scripts using uv inline metadata (PEP 723)
- ✅ Automatic environment variable injection from secrets
- ✅ Command-line argument support
- ✅ Custom working directory support
- ✅ Capture stdout and stderr
- ✅ 30-second timeout for safety

### Direct Python Execution - Multi-Skill Unification 🚀
- ✅ **UNIFY MULTIPLE SKILLS in one execution** - Combine utilities from different skills seamlessly
- ✅ **Execute Python code directly** without creating script files
- ✅ **Cross-skill imports** - Import modules from ANY skill as reusable libraries
- ✅ **Automatic dependency aggregation** - Dependencies from ALL imported skills auto-merged
- ✅ **Environment variable loading** - .env files from ALL referenced skills auto-loaded
- ✅ **PEP 723 support** - Inline dependency declarations in code
- ✅ **98.7% more efficient** - Follows Anthropic's recommended MCP pattern for scalable agents
- ✅ Perfect for multi-skill workflows, quick experiments, data analysis, and complex pipelines

### Environment Variables
- ✅ List environment variable keys (secure - no values shown)
- ✅ Set or update environment variables per skill
- ✅ Persistent storage in per-skill `.env` files
- ✅ Automatic injection into script execution

### Neo4j Knowledge Graph (Optional) 🔍
- ✅ **Graph-powered discovery** - Find related skills through relationship traversal
- ✅ **Dependency mapping** - Visualize complete dependency trees and detect conflicts
- ✅ **Impact analysis** - See what breaks if you modify a skill
- ✅ **Smart recommendations** - Find similar skills based on dependencies
- ✅ **Execution tracking** - Monitor which scripts are used and how often
- ✅ **Auto-sync** - Automatically update graph when skills change
- ✅ **Advanced queries** - Cypher queries for complex relationships
- ✅ **Visualization ready** - Export for Cytoscape.js, Neo4j Browser, and more
- ✅ **Knowledge documents** - Store tutorials, guides, and docs alongside skills
- ✅ **Unified knowledge base** - Link documentation to skills via graph relationships
- ✅ **100% optional** - Works perfectly fine without Neo4j

**See [GRAPH.md](GRAPH.md) for skills graph | [KNOWLEDGE.md](KNOWLEDGE.md) for knowledge docs**

## Directory Structure

```
~/.skill-mcp/
└── skills/                       # Your skills directory
    ├── example-skill/
    │   ├── SKILL.md             # Required: skill definition
    │   ├── .env                 # Optional: skill-specific environment variables
    │   ├── scripts/             # Optional: executable scripts
    │   ├── references/          # Optional: documentation
    │   └── assets/              # Optional: templates, files
    └── another-skill/
        ├── SKILL.md
        └── .env
```

**Note:** The MCP server is installed via `uvx` from PyPI and runs automatically. No local server file needed!

## Quick Start

### 1. Install uv

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install uv (includes uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure Your MCP Client

Add the MCP server to your configuration. The server will be automatically downloaded and run via `uvx` from PyPI.

**Claude Desktop** - Edit the config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Cursor** - Edit the config file:
- macOS: `~/.cursor/mcp.json`
- Windows: `%USERPROFILE%\.cursor\mcp.json`
- Linux: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "skill-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "skill-mcp",
        "skill-mcp-server"
      ]
    }
  }
}
```

That's it! No installation needed - `uvx` will automatically download and run the latest version from PyPI.

### 3. Restart Your MCP Client

Restart Claude Desktop or Cursor to load the MCP server.

### 4. Test It

In a new conversation:
```
List all available skills
```

Claude should use the skill-mcp tools to show skills in `~/.skill-mcp/skills/`.

## Common uv Commands

For development in this repository:
```bash
uv sync              # Install/update dependencies
uv run python script.py   # Run Python with project environment
uv add package-name  # Add a new dependency
uv pip list          # Show installed packages
uv run pytest tests/ -v   # Run tests
```

**Note:** uv automatically creates and manages `.venv/` - no need to manually create virtual environments!

## Script Dependencies (PEP 723)

**✅ BOTH `run_skill_script` AND `execute_python_code` support PEP 723!**

Python scripts and code can declare their own dependencies using uv's inline metadata. The server automatically detects this and uses `uv run` to handle dependencies:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "pandas>=2.0.0",
# ]
# ///

import requests
import pandas as pd

# Your script code here - dependencies are automatically installed!
response = requests.get("https://api.example.com/data")
df = pd.DataFrame(response.json())
print(df.head())
```

**Benefits:**
- ✅ No manual dependency installation needed
- ✅ Each script/code execution has isolated dependencies
- ✅ Works automatically with **both** `run_skill_script` and `execute_python_code`
- ✅ Version pinning ensures reproducibility
- ✅ `execute_python_code` ALSO aggregates dependencies from skill imports!

**How it works with `run_skill_script`:**
1. You add inline metadata to your Python script file
2. When the script runs via `run_skill_script`, the server detects the metadata
3. uv automatically creates an isolated environment and installs dependencies
4. The script runs with access to those dependencies
5. No manual `pip install` or virtual environment management needed!

**How it works with `execute_python_code`:**
1. Include PEP 723 metadata directly in your code string
2. The server automatically detects the metadata
3. uv creates an isolated environment and installs dependencies
4. Your code runs with access to those dependencies
5. **BONUS:** If you import from skill files, their PEP 723 dependencies are automatically aggregated too!

**Example:** See `example-skill/scripts/fetch_data.py` for a working example.

**Testing locally:**
```bash
# Scripts with dependencies just work!
uv run example-skill/scripts/fetch_data.py
```

## Direct Python Code Execution - Unify Multiple Skills in One Run

The `execute_python_code` tool allows you to run Python code that **combines multiple skills in a single execution**. This is perfect for:
- 🔄 **Multi-skill workflows** - Import and compose utilities from different skills
- 🧪 **Quick experiments** - Test code without creating files
- 📊 **Data analysis** - Process data using libraries from multiple skills
- 🏗️ **Building on reusable skill libraries** - Create specialized utilities once, use everywhere

**Key insight from Anthropic's research:** Agents scale better by writing code to call tools instead of making direct tool calls. This approach reduces context usage by up to 98.7% and enables more efficient workflows.

### Basic Usage

```python
# Simple inline execution with dependencies
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

import requests
response = requests.get("https://api.example.com/data")
print(response.json())
```

### Cross-Skill Imports - Unifying Multiple Skills

**The power of composition** - Create utility skills once and combine them in endless ways:

**Real-world example:** Process sales data by unifying calculator, data-processor, and CRM skills:

**Step 1: Create a calculator skill with reusable modules**
```python
# calculator:math_utils.py
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
```

**Step 2: Create data-processor skill utilities**
```python
# data-processor:csv_parser.py
# /// script
# dependencies = ["pandas>=2.0.0"]
# ///
import pandas as pd

def parse_csv_url(url):
    return pd.read_csv(url)

def filter_by_status(df, status):
    return df[df['status'] == status]
```

**Step 3: Unify both skills in one execution!**
```python
# Execute with skill_references: ["calculator:math_utils.py", "data-processor:csv_parser.py"]
from math_utils import calculate_average
from csv_parser import parse_csv_url, filter_by_status

# Get sales data
sales_df = parse_csv_url('https://example.com/sales.csv')

# Filter active deals
active_deals = filter_by_status(sales_df, 'active')

# Calculate average deal size using calculator skill
deal_values = active_deals['amount'].tolist()
avg_deal = calculate_average(deal_values)

print(f"Active deals: {len(active_deals)}")
print(f"Average deal size: ${avg_deal:,.2f}")
```

**What just happened:**
- ✅ **Two skills unified** - calculator + data-processor in one execution
- ✅ **Zero redundancy** - pandas dependency declared once in csv_parser.py, auto-included
- ✅ **Composable** - Mix and match any skills like LEGO blocks
- ✅ **Context-efficient** - Only loaded the specific modules needed

### Automatic Dependency Aggregation

When you import from skill modules that have PEP 723 dependencies, they're automatically included:

**Library skill with dependencies:**
```python
# data-processor:json_fetcher.py
# /// script
# dependencies = ["requests>=2.31.0"]
# ///
import requests
def fetch_json(url):
    return requests.get(url).json()
```

**Your code - NO need to redeclare requests!**
```python
# Execute with skill_references: ["data-processor:json_fetcher.py"]
from json_fetcher import fetch_json
data = fetch_json('https://api.example.com')
print(data)
# Dependencies from json_fetcher.py are automatically aggregated!
```

### Environment Variables from Referenced Skills

When you import from a skill, its environment variables are **automatically loaded**:

**Skill with API credentials:**
```bash
# weather-skill/.env
API_KEY=your-secret-api-key
API_URL=https://api.weatherapi.com
```

**Your code - env vars automatically available:**
```python
# Execute with skill_references: ["weather-skill:api_client.py"]
from api_client import fetch_weather

# api_client.py can access API_KEY and API_URL from its .env file
data = fetch_weather('London')
print(data)
```

**Benefits:**
- ✅ No need to manually load .env files
- ✅ Each skill's secrets stay isolated
- ✅ Multiple skills' env vars are merged automatically
- ✅ Later skills override earlier ones if there are conflicts

### Use Cases

- 🔄 **Multi-skill workflows** - **THE KILLER FEATURE** - Unify utilities from multiple skills in one execution
  - Example: Combine API client + data parser + analytics calculator in single run
  - Example: Chain together scraper + NLP processor + notification sender
  - Example: Merge CRM data + payment processor + reporting tools
- ✅ **Quick data analysis** - Run pandas/numpy code without creating files
- ✅ **API testing** - Test HTTP requests with inline dependencies
- ✅ **Reusable libraries** - Build once, import everywhere
- ✅ **Rapid prototyping** - Experiment with code before committing to files
- ✅ **Complex pipelines** - Build multi-stage data processing in one code block

### Comparison: `run_skill_script` vs `execute_python_code`

Both tools support PEP 723, but have different use cases:

| Feature | `run_skill_script` | `execute_python_code` |
|---------|-------------------|----------------------|
| **PEP 723 Support** | ✅ YES | ✅ YES |
| **Requires file** | ✅ Yes - executes existing script files | ❌ No - runs code directly |
| **Languages supported** | Python, JavaScript, Bash, any executable | Python only |
| **Cross-skill imports** | ❌ No - single skill only | ✅ YES - **UNIFY MULTIPLE SKILLS** |
| **Dependency aggregation** | ❌ No | ✅ YES - **auto-merges deps from all imported skills** |
| **Environment loading** | Loads skill's .env only | **Loads .env from ALL referenced skills** |
| **Context efficiency** | Standard | **98.7% token reduction** (Anthropic research) |
| **Best for** | Running complete scripts, batch jobs | **Multi-skill workflows**, quick experiments |
| **Example use case** | `python data_processor.py --input data.csv` | **`from skill1 import x; from skill2 import y; combined()`** |

**Key Insight:**
- Use `run_skill_script` when you have a script file ready to execute
- Use `execute_python_code` when you want to **UNIFY MULTIPLE SKILLS in one execution** - This is the recommended approach per [Anthropic's MCP research](https://www.anthropic.com/engineering/code-execution-with-mcp) for building efficient, scalable agents

## Usage Examples

### Creating a New Skill

```
User: "Create a new skill called 'pdf-processor' that can rotate and merge PDFs"

Claude will:
1. Create the skill directory and SKILL.md
2. Add any necessary scripts
3. Test the scripts
4. Guide you through setting up any needed dependencies
```

### Managing Environment Variables

```
User: "I need to set up a GitHub API token for my GitHub skills"

Claude will:
1. Guide you to add it to the skill's .env file
2. Use `read_skill_env` to list available keys
3. Confirm it's available for scripts to use via `os.environ`
```

### Running Skill Scripts

```
User: "Run the data processing script from my analytics skill"

Claude will:
1. List available skills and scripts
2. Execute the script with environment variables
3. Show you the output and any errors
```

### Modifying Existing Skills

```
User: "Add a new reference document about our API schema to the company-knowledge skill"

Claude will:
1. Read the existing skill structure
2. Create the new reference file
3. Update SKILL.md if needed to reference it
```

## Available MCP Tools

The server provides these unified CRUD tools to Claude:

| Tool              | Purpose | PEP 723 Support |
|-------------------|---------|-----------------|
| `skill_crud`      | Unified skill operations: list, get, create, delete, validate, list_templates | N/A |
| `skill_files_crud` | Unified file operations: read, create, update, delete (supports bulk operations) | N/A |
| `skill_env_crud`  | Unified environment variable operations: read, set, delete, clear | N/A |
| `run_skill_script` | Execute scripts (.py, .js, .sh) with automatic dependency detection | ✅ YES - Auto-detects PEP 723 in Python scripts |
| `execute_python_code` | Execute Python code directly without files (cross-skill imports) | ✅ YES - PEP 723 PLUS dependency aggregation |
| `skill_graph_crud` | Neo4j knowledge graph operations: sync, query, analyze, visualize, search (optional) | N/A |

**Key Benefits of CRUD Architecture:**
- ✅ **Reduced context window usage** - 6 tools instead of 9+
- ✅ **Consistent operation patterns** - All tools follow the same CRUD model
- ✅ **Bulk operations** - Create/update/delete multiple files atomically
- ✅ **Better error handling** - Unified error responses across all operations

## Security Features

### Path Validation
- All file paths are validated to prevent directory traversal attacks
- Paths with ".." or starting with "/" are rejected
- All operations are confined to the skill directory

### Environment Variables
- Variable values are never exposed when listing
- Stored in per-skill `.env` files
- File permissions should be restricted (chmod 600 on each .env)

### Script Execution
- 30-second timeout prevents infinite loops
- Scripts run with user's permissions (not elevated)
- Output size limits prevent memory issues
- Capture both stdout and stderr for debugging

## Troubleshooting

### "MCP server not found"
- Check that `uv` is in your PATH: `which uv` (or `where uv` on Windows)
- Verify the path to `.skill-mcp` directory is correct and absolute
- Test dependencies: `cd ~/.skill-mcp && uv run python -c "import mcp; print('OK')"`
- Ensure `pyproject.toml` exists in `~/.skill-mcp/`

### "Permission denied" errors
```bash
chmod +x ~/.skill-mcp/skill_mcp_server.py
chmod 755 ~/.skill-mcp
chmod 755 ~/.skill-mcp/skills
find ~/.skill-mcp/skills -name ".env" -exec chmod 600 {} \;
```

### Scripts failing to execute
- Check script has execute permissions
- Verify interpreter (python3, bash) is in PATH
- Use `list_env_keys` to check required variables are set
- Check stderr output from `run_skill_script`

### Environment variables not working
- Verify they're set: use `read_skill_env` for the skill
- Check the .env file exists: `cat ~/.skill-mcp/skills/<skill-name>/.env`
- Ensure your script is reading from `os.environ`

## Advanced: CRUD Tool Operations

All MCP tools follow a unified CRUD architecture with detailed descriptions:

### skill_crud Operations
- **list** - List all skills with descriptions, paths, and validation status (supports text/regex search)
- **get** - Get comprehensive skill information: SKILL.md content, all files, scripts, environment variables
- **create** - Create new skill from template (basic, python, bash, nodejs)
- **delete** - Delete a skill directory (requires confirmation)
- **validate** - Validate skill structure and get diagnostics
- **list_templates** - List all available skill templates with descriptions

### skill_files_crud Operations
- **read** - Read one or multiple files in a skill directory (supports bulk reads)
- **create** - Create one or more files (auto-creates parent directories, supports atomic bulk creation)
- **update** - Update one or more existing files (supports bulk updates)
- **delete** - Delete a file permanently (path-traversal protected, SKILL.md cannot be deleted)

### skill_env_crud Operations
- **read** - List environment variable keys for a skill (values hidden for security)
- **set** - Set one or more environment variables (merges with existing)
- **delete** - Delete one or more environment variables
- **clear** - Clear all environment variables for a skill

### Script Execution
- **run_skill_script** - Execute scripts with automatic PEP 723 dependency detection and environment variable injection
- **execute_python_code** - Execute Python code directly without files (supports PEP 723 dependencies and cross-skill imports)

## Advanced Configuration

### Custom Skills Directory

The skills directory can be customized using the `SKILL_MCP_DIR` environment variable. If not set, it defaults to `~/.skill-mcp/skills`.

**Setting via environment variable (recommended):**

```bash
# Temporarily for current session
export SKILL_MCP_DIR="/custom/path/to/skills"

# Permanently in your shell config (~/.bashrc, ~/.zshrc, etc.)
echo 'export SKILL_MCP_DIR="/custom/path/to/skills"' >> ~/.zshrc
```

**In MCP client configuration:**

For Claude Desktop or Cursor, add the environment variable to your MCP config:

```json
{
  "mcpServers": {
    "skill-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "skill-mcp",
        "skill-mcp-server"
      ],
      "env": {
        "SKILL_MCP_DIR": "/custom/path/to/skills"
      }
    }
  }
}
```

**Notes:**
- The directory will be created automatically if it doesn't exist
- Use absolute paths for the custom directory
- All skills will be stored in the configured directory
- No global secrets file; env vars are per-skill .env files

### Resource Limits

Resource limits are defined in `src/skill_mcp/core/config.py`:

```python
MAX_FILE_SIZE = 1_000_000      # File read limit (1MB)
MAX_OUTPUT_SIZE = 100_000      # Script output limit (100KB)
SCRIPT_TIMEOUT_SECONDS = 30    # Script execution timeout
```

To modify these limits, you'll need to fork the repository and adjust the constants in the config file.

## Architecture & Implementation

### Package Structure

```
src/skill_mcp/
├── server.py              # MCP server entry point
├── models.py              # Pydantic input/output models (backward compat)
├── models_crud.py         # Unified CRUD input models
├── core/
│   ├── config.py          # Configuration constants
│   └── exceptions.py      # Custom exception types
├── services/
│   ├── env_service.py     # Environment variable CRUD
│   ├── file_service.py    # File CRUD operations
│   ├── skill_service.py   # Skill discovery & metadata
│   ├── script_service.py  # Script execution & PEP 723
│   └── template_service.py # Template management
├── utils/
│   ├── path_utils.py      # Secure path validation
│   ├── yaml_parser.py     # YAML frontmatter parsing
│   └── script_detector.py # Script capability detection
└── tools/
    ├── skill_crud.py      # Unified skill CRUD tool
    ├── skill_files_crud.py # Unified file CRUD tool
    ├── skill_env_crud.py  # Unified env CRUD tool
    └── script_tools.py    # Script execution tools

tests/
├── conftest.py            # Pytest fixtures
└── 20+ test modules       # 145 tests (86% coverage passing)
```

### What's New

**Unified CRUD Architecture:**
- ✅ **3 unified CRUD tools** instead of 9+ individual tools (skill_crud, skill_files_crud, skill_env_crud)
- ✅ **Bulk operations** - Create/update/delete multiple files atomically
- ✅ **Consistent patterns** - All tools follow the same operation-based model
- ✅ **Better error handling** - Unified error responses across all operations

**Direct Python Execution (Multi-Skill Unification):**
- 🚀 **execute_python_code** - **UNIFY MULTIPLE SKILLS in one execution** (Anthropic's recommended MCP pattern)
- ✅ **Cross-skill imports** - Import modules from ANY skill as reusable libraries
- ✅ **Automatic dependency aggregation** - Dependencies from ALL imported skills auto-merged
- ✅ **Automatic environment loading** - .env files from ALL referenced skills auto-loaded
- ✅ **PEP 723 support** - Inline dependency declarations
- 📉 **98.7% token reduction** - Load skills progressively instead of all upfront

**Enhanced Features:**
- ✅ **Skill templates** - Create skills from templates (basic, python, bash, nodejs)
- ✅ **Template discovery** - List all available templates with descriptions
- ✅ **Skill validation** - Validate skill structure and get diagnostics
- ✅ **Search capabilities** - Search skills by name/description with text or regex
- ✅ **Namespaced paths** - File paths shown as "skill_name:file.py" for clarity
- ✅ **Configurable skills directory** - Use SKILL_MCP_DIR environment variable

## Test Results

### Unit Tests: 145/145 Passing ✅

**Coverage: 86% (959/1120 statements covered)**

Comprehensive test coverage across all modules:

| Module | Coverage | Key Areas |
|--------|----------|-----------|
| Core Config | 100% | All configuration constants |
| Models & CRUD Models | 100% | Input/Output validation |
| Exception Handling | 100% | All exception types |
| YAML Parser | 90% | Frontmatter parsing |
| Skill Service | 90% | Skill discovery & metadata |
| Template Service | 96% | Template management |
| File Service | 83% | File CRUD operations |
| Environment Service | 85% | Environment variable CRUD |
| Skill CRUD Tool | 91% | Unified skill operations |
| Skill Files CRUD Tool | 88% | Unified file operations |
| Skill Env CRUD Tool | 96% | Unified env operations |
| Script Detector | 85% | Script capability detection |
| Path Utils | 86% | Path validation & security |
| Server | 76% | MCP tool registration |
| Script Service | 78% | Script execution & PEP 723 |
| Script Tools | 29% | Script execution tools |

**Test Organization:**
- ✅ CRUD operations: Comprehensive tests for all operations (create, read, update, delete)
- ✅ Bulk operations: Atomic transaction tests for file operations
- ✅ Template system: Template discovery, validation, and creation
- ✅ Path security: Directory traversal prevention and validation
- ✅ PEP 723 support: Dependency detection and aggregation
- ✅ Integration tests: Full MCP server workflow testing

### Manual Tests: All Passed ✅
- ✅ List skills with YAML descriptions and search functionality
- ✅ Get comprehensive skill details with SKILL.md content
- ✅ Create skills from templates (basic, python, bash, nodejs)
- ✅ Read/create/update/delete files (single and bulk)
- ✅ Read/set/delete/clear environment variables
- ✅ Execute scripts with auto-dependencies (PEP 723)
- ✅ Execute Python code directly with cross-skill imports
- ✅ Dependency aggregation from imported skill modules
- ✅ Environment variable loading from referenced skills

## Verification Checklist

- ✅ Server imports successfully
- ✅ All 5 unified CRUD tools registered and callable
- ✅ 145/145 unit tests passing (86% coverage)
- ✅ All manual tests passing
- ✅ MCP client configuration working (Claude Desktop, Cursor)
- ✅ Package deployed to PyPI and active
- ✅ Scripts execute successfully with PEP 723 dependencies
- ✅ File operations working (including bulk operations)
- ✅ Environment variables working (CRUD operations)
- ✅ Template system working (create, list, validate)
- ✅ Direct Python execution working with cross-skill imports
- ✅ Backward compatible with existing skills

## Best Practices

### Skill Development
- Follow the standard skill structure (SKILL.md, scripts/, references/, assets/)
- Keep SKILL.md concise and focused
- Use progressive disclosure (split large docs into references)
- Test scripts immediately after creation

### Environment Variables
- Use descriptive names (API_KEY, DATABASE_URL)
- Never log or print sensitive values
- Set permissions on .env files: `chmod 600 ~/.skill-mcp/skills/<skill-name>/.env`

### Script Development
- Use meaningful exit codes (0 = success)
- Print helpful messages to stdout
- Print errors to stderr
- Include error handling
- **For Python scripts with dependencies:** Use inline metadata (PEP 723)
  ```python
  # /// script
  # dependencies = [
  #   "package-name>=version",
  # ]
  # ///
  ```
- Scripts without metadata use the system Python interpreter
- Scripts with metadata automatically get isolated environments via uv

### 🔐 Managing Sensitive Secrets Safely

To prevent LLMs from accessing your sensitive credentials:

**✅ RECOMMENDED: Update .env files directly on the file system**

```bash
# Edit the skill's .env file directly (LLM cannot access your local files)
nano ~/.skill-mcp/skills/my-skill/.env

# Add your secrets manually
API_KEY=your-actual-api-key-here
DATABASE_PASSWORD=your-password-here
OAUTH_TOKEN=your-token-here

# Secure the file
chmod 600 ~/.skill-mcp/skills/my-skill/.env
```

**Why this is important:**
- ✅ LLMs never see your sensitive values
- ✅ Secrets stay on your system only
- ✅ No risk of credentials appearing in logs or outputs
- ✅ Full control over sensitive data
- ✅ Can be used with `git-secret` or similar tools for versioning

**Workflow:**
1. Claude creates the skill structure and scripts
2. You manually add sensitive values to `.env` files
3. Claude can read the `.env` keys (without seeing values) and use them
4. Scripts access secrets via environment variables at runtime

**Example:**
```bash
# Step 1: Claude creates skill "api-client" via MCP
# You say: "Create a new skill called 'api-client'"

# Step 2: You manually secure the secrets
$ nano ~/.skill-mcp/skills/api-client/.env
API_KEY=sk-abc123def456xyz789
ENDPOINT=https://api.example.com

$ chmod 600 ~/.skill-mcp/skills/api-client/.env

# Step 3: Claude can now use the skill securely
# You say: "Run the API client script"
# Claude reads env var names only, uses them in scripts
# Your actual API key is never exposed to Claude
```

**❌ NEVER DO:**
- ❌ Tell Claude your actual API keys or passwords
- ❌ Ask Claude to set environment variables with sensitive values
- ❌ Store secrets in SKILL.md or other tracked files
- ❌ Use `update_skill_env` tool with real secrets (only for non-sensitive config)

**✅ DO:**
- ✅ Update `.env` files manually on your system
- ✅ Keep `.env` files in `.gitignore`
- ✅ Use `chmod 600` to restrict file access
- ✅ Tell Claude only the variable names (e.g., "the API key is in API_KEY")
- ✅ Keep secrets completely separate from LLM interactions

## ⚠️ Important: Verify LLM-Generated Code

When Claude or other LLMs create or modify skills and scripts using this MCP system, **always verify the generated code before running it in production**:

### Security Considerations
- ⚠️ **Always review generated code** - LLMs can make mistakes or generate suboptimal code
- ⚠️ **Check for security issues** - Look for hardcoded credentials, unsafe operations, or vulnerabilities
- ⚠️ **Test thoroughly** - Run scripts in isolated environments first
- ⚠️ **Validate permissions** - Ensure scripts have appropriate file and system permissions
- ⚠️ **Monitor dependencies** - Review any external packages installed via PEP 723

### Best Practices for LLM-Generated Skills
1. **Review before execution** - Always read through generated scripts
2. **Test in isolation** - Run in a safe environment before production use
3. **Use version control** - Track all changes with git for audit trails
4. **Implement error handling** - Add robust error handling and logging
5. **Set resource limits** - Use timeouts and resource constraints
6. **Run with minimal permissions** - Don't run skills as root or with elevated privileges
7. **Validate inputs** - Sanitize any user-provided data
8. **Audit logs** - Review what scripts actually do and track their execution

### Common Things to Check
- ❌ Hardcoded API keys, passwords, or tokens
- ❌ Unsafe file operations or path traversal risks
- ❌ Unvalidated external commands or shell injection risks
- ❌ Missing error handling or edge cases
- ❌ Resource-intensive operations without limits
- ❌ Unsafe deserialization (eval, pickle, etc.)
- ❌ Excessive permissions requested
- ❌ Untrustworthy external dependencies

### When in Doubt
- Ask Claude/LLM to explain the code
- Have another person review critical code
- Use linters and security scanning tools
- Run in containers or VMs for isolation
- Start with read-only operations before destructive ones

**Remember:** LLM-generated code is a starting point. Your verification and review are essential for security and reliability.

## Installation from PyPI

To install the package globally (optional):

```bash
pip install skill-mcp
```

Or use `uvx` to run without installation (recommended):

```bash
uvx --from skill-mcp skill-mcp-server
```

## Development Setup

If you want to contribute or run from source:

```bash
# Clone the repository
git clone https://github.com/fkesheh/skill-mcp.git
cd skill-mcp

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run the server locally
uv run -m skill_mcp.server
```

To use your local development version in your MCP client config:

```json
{
  "mcpServers": {
    "skill-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/skill-mcp",
        "-m",
        "skill_mcp.server"
      ]
    }
  }
}
```

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

This is a custom tool for personal use. Feel free to fork and adapt for your needs.

## Support

For setup issues or questions, refer to:
- Claude's MCP documentation at https://modelcontextprotocol.io
- The MCP Python SDK docs at https://github.com/modelcontextprotocol/python-sdk
