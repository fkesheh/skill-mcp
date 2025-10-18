# Skill Management MCP Server

A Model Context Protocol (MCP) server that enables Claude to manage skills stored in `~/.skill-mcp/skills`. This system allows Claude to create, edit, run, and manage skills programmatically, including execution of skill scripts with environment variables.

## Quick Status

**Status:** ✅ Production Ready  
**Test Coverage:** 82% (78/78 tests passing)  
**Deployed:** October 18, 2025  
**Architecture:** 19-module modular Python package

## Overview

This project consists of two main components:

1. **MCP Server** (`src/skill_mcp/server.py`) - A refactored Python package providing 9 tools for skill management
2. **Skills Directory** (`~/.skill-mcp/skills/`) - Where you store and manage your skills

## Key Advantages

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

### Environment Variables
- ✅ List environment variable keys (secure - no values shown)
- ✅ Set or update environment variables
- ✅ Persistent storage in `~/.skill-mcp/secrets`
- ✅ Automatic injection into script execution

## Directory Structure

```
~/.skill-mcp/
├── skill_mcp_server.py          # The MCP server (you install this)
├── secrets                       # Environment variables (JSON format)
└── skills/                       # Your skills directory
    ├── example-skill/
    │   ├── SKILL.md             # Required: skill definition
    │   ├── scripts/             # Optional: executable scripts
    │   ├── references/          # Optional: documentation
    │   └── assets/              # Optional: templates, files
    └── another-skill/
        └── SKILL.md
```

## Quick Start

### 1. Install uv

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install the MCP Server

```bash
# Create directory
mkdir -p ~/.skill-mcp

# Copy all project files
cp -r src tests pyproject.toml ~/.skill-mcp/

# Install dependencies (uv auto-creates .venv)
cd ~/.skill-mcp
uv sync
```

### 3. Configure Claude

Add the MCP server to your Claude configuration:

**Claude Desktop** - Edit the config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skill-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/yourname/.skill-mcp",
        "-m",
        "skill_mcp.server"
      ]
    }
  }
}
```

**Important:** Replace `/Users/yourname/.skill-mcp` with your actual absolute path!

**claude.ai** - Use the web interface:
1. Go to Settings > Developer > MCP Servers
2. Add new MCP server with the same configuration

### 4. Restart Claude

Restart Claude Desktop or refresh claude.ai to load the new MCP server.

### 5. Test It

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

Python scripts can declare their own dependencies using uv's inline metadata. The server automatically detects this and uses `uv run` to handle dependencies:

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
- ✅ Each script has isolated dependencies
- ✅ Works automatically when run via `run_skill_script`
- ✅ Version pinning ensures reproducibility

**How it works:**
1. You add inline metadata to your Python script
2. When the script runs via `run_skill_script`, the server detects the metadata
3. uv automatically creates an isolated environment and installs dependencies
4. The script runs with access to those dependencies
5. No manual `pip install` or virtual environment management needed!

**Example:** See `example-skill/scripts/fetch_data.py` for a working example.

**Testing locally:**
```bash
# Scripts with dependencies just work!
uv run example-skill/scripts/fetch_data.py
```

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
1. Ask for your token value
2. Store it securely using set_env
3. Confirm it's available for scripts to use
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

The server provides these tools to Claude:

| Tool | Purpose |
|------|---------|
| `list_skills` | List all skills in ~/.skill-mcp/skills |
| `get_skill_files` | List files in a specific skill |
| `read_skill_file` | Read content of a skill file |
| `create_skill_file` | Create a new file in a skill |
| `update_skill_file` | Update an existing skill file |
| `delete_skill_file` | Delete a skill file |
| `run_skill_script` | Execute a script with environment variables |
| `list_env_keys` | List environment variable names |
| `set_env` | Set an environment variable |

## Security Features

### Path Validation
- All file paths are validated to prevent directory traversal attacks
- Paths with ".." or starting with "/" are rejected
- All operations are confined to the skill directory

### Environment Variables
- Variable values are never exposed when listing
- Stored in a separate secrets file
- File permissions should be restricted (chmod 600)

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
chmod 600 ~/.skill-mcp/secrets
```

### Scripts failing to execute
- Check script has execute permissions
- Verify interpreter (python3, bash) is in PATH
- Use `list_env_keys` to check required variables are set
- Check stderr output from `run_skill_script`

### Environment variables not working
- Verify they're set: use `list_env_keys`
- Check the secrets file exists: `cat ~/.skill-mcp/secrets`
- Ensure your script is reading from `os.environ`

## Advanced: Tool Descriptions for LLMs

All MCP tools have been enhanced with detailed descriptions to prevent confusion:

### Skill Tools
- **list_skills** - Lists all skills with descriptions, paths, and validation status
- **get_skill_details** - Complete skill information: SKILL.md content, all files, scripts, environment variables

### File Tools
- **read_skill_file** - Read any file in a skill directory
- **create_skill_file** - Create new files (auto-creates parent directories)
- **update_skill_file** - Update existing files (replaces entire content)
- **delete_skill_file** - Delete files permanently (path-traversal protected)

### Script Tools
- **run_skill_script** - Execute scripts with automatic PEP 723 dependency detection
- **read_skill_env** - List environment variables (keys only, values hidden for security)
- **update_skill_env** - Create/update skill's .env file

## Advanced Configuration

### Custom Directories

Edit `skill_mcp_server.py` to change default locations:

```python
# Change skills directory
SKILLS_DIR = Path("/custom/path/to/skills")

# Change secrets file location
SECRETS_FILE = Path("/custom/path/to/secrets")
```

### Resource Limits

Adjust limits in `skill_mcp_server.py`:

```python
MAX_FILE_SIZE = 1_000_000      # File read limit (1MB)
MAX_OUTPUT_SIZE = 100_000      # Script output limit (100KB)
```

Script timeout in the `run_skill_script` function:

```python
result = subprocess.run(cmd, timeout=30)  # 30 seconds
```

## Architecture & Implementation

### Package Structure

```
src/skill_mcp/
├── server.py              # MCP server entry point
├── models.py              # Pydantic input/output models
├── core/
│   ├── config.py          # Configuration constants
│   └── exceptions.py      # Custom exception types
├── services/
│   ├── env_service.py     # .env file management
│   ├── file_service.py    # File operations
│   ├── skill_service.py   # Skill discovery & metadata
│   └── script_service.py  # Script execution
├── utils/
│   ├── path_utils.py      # Secure path validation
│   ├── yaml_parser.py     # YAML frontmatter parsing
│   └── script_detector.py # Script capability detection
└── tools/
    ├── skill_tools.py     # Skill management tools
    ├── file_tools.py      # File operation tools
    └── script_tools.py    # Script execution tools

tests/
├── conftest.py            # Pytest fixtures
└── 9 test modules         # 78 tests (82% coverage passing)
```

### What's New

**Enhanced Features:**
- ✅ Skill descriptions extracted from YAML frontmatter
- ✅ Comprehensive skill details (files, scripts, metadata)
- ✅ File type detection (Python, Markdown, etc.)
- ✅ Executable identification with metadata
- ✅ **PEP 723 uv dependency detection** - scripts declare own dependencies
- ✅ Per-skill environment variables (.env files)
- ✅ Automatic dependency management for scripts

**Breaking Changes:**
- Removed global `~/.skill-mcp/secrets` (now per-skill .env files)
- Removed `list_env_keys` and `set_env` global tools
- Replaced `get_skill_files` with more comprehensive `get_skill_details`

## Test Results

### Unit Tests: 78/78 Passing ✅

**Coverage: 82% (522/641 statements covered)**

Comprehensive test coverage across all modules:

| Module | Coverage | Tests |
|--------|----------|-------|
| Core Config | 100% | All paths |
| Models | 100% | Input/Output validation |
| Exception Handling | 100% | All exception types |
| YAML Parser | 90% | Frontmatter parsing |
| Skill Service | 90% | Skill discovery & metadata |
| File Service | 89% | File operations |
| Environment Service | 83% | .env management |
| Skill Tools | 85% | Skill management tools |
| File Tools | 79% | File operation tools |
| Script Detector | 87% | Script capability detection |
| Path Utils | 86% | Path validation & security |
| Server | 67% | MCP tool registration |
| Script Service | 53% | Script execution |
| Script Tools | 61% | Script execution tools |

**Test Breakdown:**
- ✅ Path utilities: 4 tests
- ✅ YAML parsing: 7 tests
- ✅ Environment service: 7 tests
- ✅ File service: 4 tests
- ✅ Skill service: 5 tests
- ✅ Script detector: 20 tests
- ✅ Script service: 7 tests
- ✅ Integration tests: 24 tests

### Manual Tests: All Passed ✅
- ✅ List skills with YAML descriptions
- ✅ Get comprehensive skill details with SKILL.md content
- ✅ Read/create/update/delete files
- ✅ Read/update environment variables
- ✅ Execute scripts with auto-dependencies
- ✅ Weather-fetcher example runs successfully

## Verification Checklist

- ✅ Server imports successfully
- ✅ All 9 tools registered and callable
- ✅ 78/78 unit tests passing (82% coverage)
- ✅ All manual tests passing
- ✅ .cursor/mcp.json configured
- ✅ Package deployed and active
- ✅ Scripts execute successfully
- ✅ File operations working
- ✅ Environment variables working
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
- Set permissions on secrets file: `chmod 600 ~/.skill-mcp/skills/skillname/.env`

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
