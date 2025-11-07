"""Script execution tools for MCP server."""

from mcp import types
from skill_mcp.models import RunSkillScriptInput
from skill_mcp.services.script_service import ScriptService
from skill_mcp.core.exceptions import SkillMCPException


class ScriptTools:
    """Tools for script execution."""

    @staticmethod
    def get_script_tools() -> list[types.Tool]:
        """Get script execution tools."""
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
