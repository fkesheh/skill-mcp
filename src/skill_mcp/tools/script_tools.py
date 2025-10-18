"""Script execution tools for MCP server."""

from mcp import types
from skill_mcp.models import (
    RunSkillScriptInput,
    ReadSkillEnvInput,
    UpdateSkillEnvInput,
)
from skill_mcp.services.script_service import ScriptService
from skill_mcp.services.env_service import EnvironmentService
from skill_mcp.core.exceptions import SkillMCPException


class ScriptTools:
    """Tools for script execution and environment management."""
    
    @staticmethod
    def get_script_tools() -> list[types.Tool]:
        """Get script and environment tools."""
        return [
            types.Tool(
                name="run_skill_script",
                description="""Execute a script or executable program within a skill directory with optional arguments and automatic dependency management.

This tool runs scripts in multiple languages and automatically manages dependencies:

SUPPORTED LANGUAGES:
- Python: Automatically installs PEP 723 inline dependencies via 'uv run' if declared in the script
- Bash: Executes shell scripts (.sh files)
- Other: Any executable file with proper shebang line

FEATURES:
- Automatic dependency installation: Python scripts with PEP 723 metadata (/* script */ dependencies) are run with 'uv run' automatically
- Environment variables: Loads skill-specific .env file and injects variables into script environment
- Working directory: Can specify a subdirectory to run the script from
- Arguments: Pass command-line arguments to the script
- Output capture: Returns stdout, stderr, and exit code

PARAMETERS:
- skill_name: The name of the skill directory (e.g., 'weather-skill')
- script_path: Relative path to the script (e.g., 'scripts/fetch_weather.py', 'bin/process.sh')
- args: Optional list of command-line arguments to pass to the script (e.g., ['--verbose', 'input.txt'])
- working_dir: Optional working directory for execution (relative to skill root)

BEHAVIOR:
- Python scripts with PEP 723 metadata are detected automatically and run with 'uv run'
- Environment variables from skill's .env file are available to the script
- Script must be executable or have proper shebang line
- Script path is relative to the skill directory

RETURNS: Script execution result with:
- Exit code (0 = success, non-zero = failure)
- STDOUT (standard output)
- STDERR (error output)""",
                inputSchema=RunSkillScriptInput.model_json_schema(),
            ),
            types.Tool(
                name="read_skill_env",
                description="""Read and list all environment variable keys defined in a skill's .env file.

This tool helps you understand what environment variables are configured for a skill:
- Lists only the KEY names (values are hidden for security)
- Shows whether a .env file exists for the skill
- Returns an empty message if no variables are set

PARAMETERS:
- skill_name: The name of the skill directory

USE CASES:
- Check what environment variables a skill needs before running scripts
- Verify that required credentials or API keys are configured
- Understand the expected configuration for a skill
- Debug missing environment variables

SECURITY NOTE:
- Environment variable VALUES are intentionally hidden and not returned
- This prevents accidental exposure of secrets or credentials
- To set or update variables, use update_skill_env tool

RETURNS: A list of environment variable key names (e.g., API_KEY, DATABASE_URL)""",
                inputSchema=ReadSkillEnvInput.model_json_schema(),
            ),
            types.Tool(
                name="update_skill_env",
                description="""Create, update, or replace the .env file for a skill with new environment variables.

This tool manages skill-specific environment variables used by scripts:

PARAMETERS:
- skill_name: The name of the skill directory
- content: The complete .env file content in KEY=VALUE format

FORMAT:
Each line should be: KEY=VALUE
Example:
  API_KEY=sk-abc123def456
  DATABASE_URL=postgres://user:pass@localhost:5432/db
  DEBUG=true
  TIMEOUT=30

BEHAVIOR:
- Replaces the ENTIRE .env file with the content you provide
- Creates the .env file if it doesn't exist
- Each line should follow KEY=VALUE format (one per line)
- Comments starting with # are allowed
- Empty lines are allowed
- These variables become available to all scripts run in this skill

IMPORTANT:
- Values will be stored as plain text, so don't commit sensitive values to git
- Use the QUICKSTART.md for instructions on setting up secrets safely
- After updating, use read_skill_env to verify keys were set correctly

SECURITY:
- Keep .env files in .gitignore to prevent accidental commits of secrets
- Use environment variables for all sensitive data (API keys, passwords, tokens)
- Never hardcode secrets in scripts

RETURNS: Success message confirming the .env file was updated""",
                inputSchema=UpdateSkillEnvInput.model_json_schema(),
            ),
        ]
    
    @staticmethod
    async def run_skill_script(input_data: RunSkillScriptInput) -> list[types.TextContent]:
        """Execute a skill script."""
        try:
            result = await ScriptService.run_script(
                input_data.skill_name,
                input_data.script_path,
                input_data.args,
                input_data.working_dir
            )
            
            output = f"Script: {input_data.skill_name}/{input_data.script_path}\n"
            output += f"Exit code: {result.exit_code}\n\n"
            
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            
            if not result.stdout and not result.stderr:
                output += "(No output)\n"
            
            return [types.TextContent(type="text", text=output)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error running script: {str(e)}")]
    
    @staticmethod
    async def read_skill_env(input_data: ReadSkillEnvInput) -> list[types.TextContent]:
        """Read skill's .env file - returns only keys, not values."""
        try:
            keys = EnvironmentService.get_env_keys(input_data.skill_name)
            
            if not keys:
                result = f"No environment variables set for skill '{input_data.skill_name}'"
            else:
                keys_str = "\n".join(f"- {key}" for key in keys)
                result = f"Environment variable keys for skill '{input_data.skill_name}':\n\n{keys_str}"
            
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading .env: {str(e)}")]
    
    @staticmethod
    async def update_skill_env(input_data: UpdateSkillEnvInput) -> list[types.TextContent]:
        """Update skill's .env file."""
        try:
            EnvironmentService.update_env_file(input_data.skill_name, input_data.content)
            result = f"Successfully updated .env file for skill '{input_data.skill_name}'"
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error updating .env: {str(e)}")]
