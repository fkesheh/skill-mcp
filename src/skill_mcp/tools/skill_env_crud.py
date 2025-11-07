"""Unified environment variable CRUD tool for MCP server."""

from mcp import types
from skill_mcp.models_crud import SkillEnvCrudInput
from skill_mcp.services.env_service import EnvironmentService
from skill_mcp.core.exceptions import SkillNotFoundError, EnvFileError


class SkillEnvCrud:
    """Unified tool for skill environment variable CRUD operations."""

    @staticmethod
    def get_tool_definition() -> list[types.Tool]:
        """Get tool definition."""
        return [
            types.Tool(
                name="skill_env_crud",
                description="""Unified CRUD tool for skill environment variable operations. Supports single and bulk operations.

**Operations:**
- **read**: Read all environment variable keys (values are hidden for security)
- **set**: Set one or more environment variables (smart merge by default)
- **delete**: Delete one or more environment variables
- **clear**: Clear all environment variables

**Read Example:**
```python
# Read all env var keys
{"operation": "read", "skill_name": "my-skill"}
```

**Set Examples:**
```python
# Set single variable (smart mode - merges with existing)
{
  "operation": "set",
  "skill_name": "my-skill",
  "variables": {"API_KEY": "sk-123"},
  "mode": "smart"
}

# Set multiple variables (bulk)
{
  "operation": "set",
  "skill_name": "my-skill",
  "variables": {
    "API_KEY": "sk-123",
    "DEBUG": "true",
    "TIMEOUT": "30"
  },
  "mode": "merge"
}

# Replace entire .env file
{
  "operation": "set",
  "skill_name": "my-skill",
  "variables": {"API_KEY": "sk-123"},
  "mode": "replace"
}
```

**Delete Examples:**
```python
# Delete single variable
{
  "operation": "delete",
  "skill_name": "my-skill",
  "keys": ["API_KEY"]
}

# Delete multiple variables (bulk)
{
  "operation": "delete",
  "skill_name": "my-skill",
  "keys": ["API_KEY", "DEBUG", "TIMEOUT"]
}
```

**Clear Example:**
```python
# Clear all environment variables
{"operation": "clear", "skill_name": "my-skill"}
```

**Modes:**
- **smart** (default): Auto-detect if incremental (single var) or full replacement
- **merge**: Merge with existing, preserving comments and other variables
- **replace**: Replace entire .env file

**Context Window Optimization:** This single tool replaces 2 separate tools (read_skill_env, update_skill_env).""",
                inputSchema=SkillEnvCrudInput.model_json_schema(),
            )
        ]

    @staticmethod
    async def skill_env_crud(input_data: SkillEnvCrudInput) -> list[types.TextContent]:
        """Handle environment variable CRUD operations."""
        operation = input_data.operation

        try:
            if operation == "read":
                return await SkillEnvCrud._handle_read(input_data)
            elif operation == "set":
                return await SkillEnvCrud._handle_set(input_data)
            elif operation == "delete":
                return await SkillEnvCrud._handle_delete(input_data)
            elif operation == "clear":
                return await SkillEnvCrud._handle_clear(input_data)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Unknown operation: {operation}. Valid operations: read, set, delete, clear"
                )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    @staticmethod
    async def _handle_read(input_data: SkillEnvCrudInput) -> list[types.TextContent]:
        """Handle read operation."""
        keys = EnvironmentService.get_env_keys(input_data.skill_name)

        if not keys:
            result = f"No environment variables set for skill '{input_data.skill_name}'"
        else:
            result = f"Environment variables for skill '{input_data.skill_name}' ({len(keys)}):\n"
            for key in keys:
                result += f"  - {key}\n"
            result += "\nNote: Values are hidden for security. Use read_env_file() to see the raw .env content."

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_set(input_data: SkillEnvCrudInput) -> list[types.TextContent]:
        """Handle set operation (single or bulk)."""
        if not input_data.variables:
            return [types.TextContent(type="text", text="Error: variables is required for 'set' operation")]

        mode = input_data.mode or "smart"
        var_count = len(input_data.variables)

        # Determine actual mode - for smart mode with many vars, use replace
        if mode == "smart" and var_count > 5:
            actual_mode = "replace"
        elif mode == "smart":
            actual_mode = "merge"
        else:
            actual_mode = mode

        EnvironmentService.set_variables(input_data.skill_name, input_data.variables, actual_mode)

        return [types.TextContent(
            type="text",
            text=f"Successfully set {var_count} environment variable(s) for skill '{input_data.skill_name}' (mode: {actual_mode})"
        )]

    @staticmethod
    async def _handle_delete(input_data: SkillEnvCrudInput) -> list[types.TextContent]:
        """Handle delete operation (single or bulk)."""
        if not input_data.keys:
            return [types.TextContent(type="text", text="Error: keys is required for 'delete' operation")]

        EnvironmentService.delete_variables(input_data.skill_name, input_data.keys)

        return [types.TextContent(
            type="text",
            text=f"Successfully deleted {len(input_data.keys)} environment variable(s) from skill '{input_data.skill_name}'"
        )]

    @staticmethod
    async def _handle_clear(input_data: SkillEnvCrudInput) -> list[types.TextContent]:
        """Handle clear operation."""
        EnvironmentService.clear_env(input_data.skill_name)

        return [types.TextContent(
            type="text",
            text=f"Successfully cleared all environment variables for skill '{input_data.skill_name}'"
        )]
