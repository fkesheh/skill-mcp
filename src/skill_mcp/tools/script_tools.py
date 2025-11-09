"""Script execution tools for MCP server."""

from mcp import types

from skill_mcp.core.exceptions import SkillMCPException
from skill_mcp.models import RunSkillScriptInput
from skill_mcp.services.script_service import ScriptService


class ScriptTools:
    """Tools for script execution."""

    @staticmethod
    def get_script_tools() -> list[types.Tool]:
        """Get script execution tools."""
        return [
            types.Tool(
                name="run_skill_script",
                description="""Execute a script or executable program within a skill directory with optional arguments and automatic dependency management.

IMPORTANT: ALWAYS use this tool to execute scripts. DO NOT use external bash/shell tools to execute scripts directly. This tool provides:
- Automatic dependency management (Python PEP 723, npm packages)
- Proper environment variable injection from .env files
- Secure execution within skill directory boundaries
- Proper error handling and output capture

SUPPORTED LANGUAGES:
- Python: Automatically installs PEP 723 inline dependencies via 'uv run' if declared in the script
- JavaScript/Node.js: Automatically runs 'npm install' if package.json exists
- Bash: Executes shell scripts (.sh files)
- Other: Any executable file with proper shebang line

FEATURES:
- Automatic dependency installation: Python scripts with PEP 723 metadata are run with 'uv run', Node.js scripts install npm dependencies
- Environment variables: Loads skill-specific .env file and injects variables into script environment
- Working directory: Can specify a subdirectory to run the script from
- Arguments: Pass command-line arguments to the script
- Output capture: Returns stdout, stderr, and exit code

PARAMETERS:
- skill_name: The name of the skill directory (e.g., 'weather-skill')
- script_path: Relative path to the script within skill directory (e.g., 'main.py', 'scripts/fetch_weather.py', 'bin/process.sh')
- args: Optional list of command-line arguments (e.g., ['--verbose', 'input.txt'])
- working_dir: Optional working directory relative to skill root (e.g., 'scripts')

IMPORTANT PATH NOTES:
- All paths are RELATIVE to the skill directory, never absolute paths
- Script path example: 'main.py' NOT '/Users/username/.skill-mcp/skills/my-skill/main.py'
- Working dir example: 'scripts' NOT '/full/path/to/scripts'

RETURNS: Script execution result with:
- Exit code (0 = success, non-zero = failure)
- STDOUT (standard output)
- STDERR (error output)""",
                inputSchema=RunSkillScriptInput.model_json_schema(),
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
                input_data.working_dir,
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
