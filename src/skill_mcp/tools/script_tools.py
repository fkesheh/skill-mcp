"""Script execution tools for MCP server."""

from mcp import types

from skill_mcp.core.exceptions import SkillMCPException
from skill_mcp.models import ExecutePythonCodeInput, RunSkillScriptInput
from skill_mcp.services.script_service import ScriptService


class ScriptTools:
    """Tools for script execution."""

    @staticmethod
    def get_script_tools() -> list[types.Tool]:
        """Get script execution tools."""
        return [
            types.Tool(
                name="execute_python_code",
                description="""Execute Python code directly without requiring a script file.

RECOMMENDATION: Prefer Python over bash/shell scripts for better portability, error handling, and maintainability.

IMPORTANT: Use this tool instead of creating temporary script files when you need to run quick Python code.

✅ SUPPORTS PEP 723 INLINE DEPENDENCIES - just like run_skill_script!

FEATURES:
- **PEP 723 inline dependencies**: Include dependencies directly in code using /// script comments (auto-detected and installed)
- **Dependency aggregation**: When importing from skills, their PEP 723 dependencies are automatically merged into your code
- Skill file imports: Reference files from skills using namespace format (skill_name:path/to/file.py)
- Automatic dependency installation: Code with PEP 723 metadata is run with 'uv run'
- Environment variable loading: Automatically loads .env files from all referenced skills
- Clean execution: Temporary file is automatically cleaned up after execution

PARAMETERS:
- code: Python code to execute (can include PEP 723 dependencies)
- skill_references: Optional list of skill files to make available for import
                   Format: ["calculator:utils.py", "weather:api/client.py"]
                   The skill directories will be added to PYTHONPATH
                   Environment variables from each skill's .env file will be loaded
- timeout: Optional timeout in seconds (defaults to 30 seconds if not specified)

CROSS-SKILL IMPORTS - BUILD REUSABLE LIBRARIES:
Create utility skills once, import them anywhere! Perfect for:
- Math/statistics libraries (calculator:stats.py)
- API clients (weather:api_client.py)
- Data processors (etl:transformers.py)
- Common utilities (helpers:string_utils.py)

AUTOMATIC DEPENDENCY AGGREGATION:
When you reference skill files, their PEP 723 dependencies are automatically collected
and merged into your code! You don't need to redeclare dependencies - just reference
the modules and their deps are included automatically.

Example - library module with deps:
```python
# data-processor:json_fetcher.py
# /// script
# dependencies = ["requests>=2.31.0"]
# ///
import requests
def fetch_json(url): return requests.get(url).json()
```

Your code - NO need to declare requests!
```json
{
  "code": "from json_fetcher import fetch_json\\ndata = fetch_json('https://api.example.com')\\nprint(data)",
  "skill_references": ["data-processor:json_fetcher.py"]
}
```
Dependencies from json_fetcher.py are automatically aggregated!

Import from single skill:
```json
{
  "code": "from math_utils import add, multiply\\nprint(add(10, 20))",
  "skill_references": ["calculator:math_utils.py"]
}
```

Import from multiple skills:
```json
{
  "code": "from math_utils import add\\nfrom stats_utils import mean\\nfrom converters import celsius_to_fahrenheit\\n\\nresult = add(10, 20)\\navg = mean([10, 20, 30])\\ntemp = celsius_to_fahrenheit(25)\\nprint(f'Sum: {result}, Avg: {avg}, Temp: {temp}F')",
  "skill_references": ["calculator:math_utils.py", "calculator:stats_utils.py", "calculator:converters.py"]
}
```

Import from subdirectories:
```json
{
  "code": "from advanced.calculus import derivative_at_point\\ndef f(x): return x**2\\nprint(derivative_at_point(f, 5))",
  "skill_references": ["calculator:advanced/calculus.py"]
}
```

ENVIRONMENT VARIABLES FROM REFERENCED SKILLS:
When you import from a skill, its environment variables are automatically loaded:
```json
{
  "code": "from api_client import fetch_weather\\ndata = fetch_weather('London')\\nprint(data)",
  "skill_references": ["weather:api_client.py"]
}
```
If weather:api_client.py uses API_KEY from its .env file, it will be available automatically!

EXAMPLE WITH PEP 723 DEPENDENCIES:
```json
{
  "code": "# /// script\\n# dependencies = [\\n#   \\"requests>=2.31.0\\",\\n#   \\"pandas\\",\\n# ]\\n# ///\\n\\nimport requests\\nimport pandas as pd\\n\\nresponse = requests.get('https://api.example.com/data')\\ndf = pd.DataFrame(response.json())\\nprint(df.head())"
}
```

WHY PYTHON OVER BASH/JS:
- Better error handling and debugging
- Rich standard library
- Cross-platform compatibility
- Easier to read and maintain
- Strong typing support
- Better dependency management

RETURNS: Execution result with:
- Exit code (0 = success, non-zero = failure)
- STDOUT (standard output)
- STDERR (error output)""",
                inputSchema=ExecutePythonCodeInput.model_json_schema(),
            ),
            types.Tool(
                name="run_skill_script",
                description="""Execute a script within a skill directory. Skills are modular libraries with reusable code - scripts can import from their own modules or use external dependencies.

IMPORTANT: ALWAYS use this tool to execute scripts. DO NOT use external bash/shell tools to execute scripts directly. This tool provides:
- Automatic dependency management (Python PEP 723, npm packages)
- Proper environment variable injection from .env files
- Secure execution within skill directory boundaries
- Proper error handling and output capture

SKILLS AS LIBRARIES:
Scripts within a skill can import from local modules naturally:
```
weather-skill/
├── main.py          # Script that imports from modules below
├── api_client.py    # Reusable API client module
├── parsers.py       # Data parsing utilities
└── formatters.py    # Output formatting
```

In main.py:
```python
from api_client import WeatherAPI
from formatters import format_temperature

api = WeatherAPI()
data = api.get_weather("London")
print(format_temperature(data))
```

Execute with:
```json
{
  "skill_name": "weather-skill",
  "script_path": "main.py",
  "args": ["--city", "London"]
}
```

SUPPORTED LANGUAGES:
- Python: Automatically detects and installs PEP 723 inline dependencies via 'uv run'
- JavaScript/Node.js: Automatically runs 'npm install' if package.json exists
- Bash: Executes shell scripts (.sh files)
- Other: Any executable file with proper shebang line

FEATURES:
- Module imports: Scripts can import from other files within the skill directory
- **Automatic PEP 723 dependency detection**: Python scripts with inline metadata are automatically run with 'uv run'
- Automatic npm dependency installation: Node.js scripts install dependencies from package.json
- Environment variables: Loads skill-specific .env file and injects variables into script environment
- Working directory: Can specify a subdirectory to run the script from
- Arguments: Pass command-line arguments to the script
- Output capture: Returns stdout, stderr, and exit code

PEP 723 AUTOMATIC DEPENDENCY DETECTION:
Python scripts with inline dependencies are automatically detected and executed with 'uv run':

Example Python script with PEP 723 (e.g., weather-skill/fetch_weather.py):
```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "beautifulsoup4>=4.12.0",
# ]
# ///

import requests
from bs4 import BeautifulSoup

response = requests.get("https://api.weather.com/data")
print(response.json())
```

Execute with automatic dependency handling:
```json
{
  "skill_name": "weather-skill",
  "script_path": "fetch_weather.py",
  "args": ["--city", "London"]
}
```

No manual dependency installation needed - the server automatically:
1. Detects the PEP 723 metadata in your script
2. Uses 'uv run' to create an isolated environment
3. Installs the declared dependencies
4. Executes your script with access to those dependencies

PARAMETERS:
- skill_name: The name of the skill directory (e.g., 'weather-skill')
- script_path: Relative path to the script within skill directory (e.g., 'main.py', 'scripts/fetch_weather.py', 'bin/process.sh')
- args: Optional list of command-line arguments (e.g., ['--verbose', 'input.txt'])
- working_dir: Optional working directory relative to skill root (e.g., 'scripts')
- timeout: Optional timeout in seconds (defaults to 30 seconds if not specified)

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
    async def execute_python_code(
        input_data: ExecutePythonCodeInput,
    ) -> list[types.TextContent]:
        """Execute Python code directly."""
        try:
            result = await ScriptService.execute_python_code(
                input_data.code,
                input_data.skill_references,
                input_data.timeout,
            )

            output = "Python Code Execution\n"
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
            return [types.TextContent(type="text", text=f"Error executing code: {str(e)}")]

    @staticmethod
    async def run_skill_script(input_data: RunSkillScriptInput) -> list[types.TextContent]:
        """Execute a skill script."""
        try:
            result = await ScriptService.run_script(
                input_data.skill_name,
                input_data.script_path,
                input_data.args,
                input_data.working_dir,
                input_data.timeout,
                input_data.script_node_id,
            )

            # Track script execution in graph if enabled
            from skill_mcp.core.config import GRAPH_ENABLED

            if GRAPH_ENABLED:
                try:
                    from datetime import datetime

                    from skill_mcp.services.graph_service import GraphService

                    graph_service = GraphService()
                    await graph_service.record_script_execution(
                        skill_name=input_data.skill_name,
                        script_path=input_data.script_path,
                        success=(result.exit_code == 0),
                        timestamp=datetime.now(),
                    )
                except Exception:
                    # Silently fail - don't break script execution
                    pass

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
