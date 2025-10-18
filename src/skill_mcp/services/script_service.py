"""Script execution service."""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from skill_mcp.core.config import SKILLS_DIR, SCRIPT_TIMEOUT_SECONDS, MAX_OUTPUT_SIZE, DEFAULT_PYTHON_INTERPRETER
from skill_mcp.core.exceptions import SkillNotFoundError, InvalidPathError, ScriptExecutionError
from skill_mcp.utils.path_utils import validate_path
from skill_mcp.utils.script_detector import has_uv_dependencies
from skill_mcp.services.env_service import EnvironmentService


class ScriptResult:
    """Result of script execution."""
    
    def __init__(self, exit_code: int, stdout: str, stderr: str):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "success": self.exit_code == 0
        }


class ScriptService:
    """Service for executing skill scripts."""
    
    @staticmethod
    async def run_script(
        skill_name: str,
        script_path: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ) -> ScriptResult:
        """
        Execute a script with skill's environment variables.
        
        Args:
            skill_name: Name of the skill
            script_path: Relative path to the script
            args: Optional command-line arguments
            working_dir: Optional working directory
            
        Returns:
            ScriptResult object
            
        Raises:
            InvalidPathError: If path is invalid
            SkillNotFoundError: If skill doesn't exist
            ScriptExecutionError: If execution fails
        """
        # Validate script path
        try:
            full_script_path = validate_path(skill_name, script_path)
        except (InvalidPathError, Exception) as e:
            raise InvalidPathError(f"Invalid script path: {str(e)}")
        
        if not full_script_path.exists():
            raise ScriptExecutionError(
                f"Script '{script_path}' does not exist in skill '{skill_name}'"
            )
        
        if not full_script_path.is_file():
            raise ScriptExecutionError(f"'{script_path}' is not a file")
        
        # Load skill environment variables
        try:
            skill_env = EnvironmentService.load_skill_env(skill_name)
        except SkillNotFoundError:
            raise
        except Exception:
            skill_env = {}
        
        # Build environment
        env = os.environ.copy()
        env.update(skill_env)
        
        # Determine working directory
        if working_dir:
            try:
                work_dir_path = validate_path(skill_name, working_dir)
                if not work_dir_path.is_dir():
                    raise ScriptExecutionError(
                        f"Working directory '{working_dir}' is not a directory"
                    )
            except InvalidPathError as e:
                raise ScriptExecutionError(f"Invalid working directory: {str(e)}")
            work_dir = str(work_dir_path)
        else:
            work_dir = str(SKILLS_DIR / skill_name)
        
        # Build command
        args = args or []
        ext = full_script_path.suffix.lower()
        
        if ext == ".py":
            # Check if script has uv metadata (PEP 723)
            if has_uv_dependencies(full_script_path):
                cmd = ["uv", "run", str(full_script_path)] + args
            else:
                cmd = [DEFAULT_PYTHON_INTERPRETER, str(full_script_path)] + args
        elif ext == ".sh":
            cmd = ["bash", str(full_script_path)] + args
        else:
            # Try to execute directly
            cmd = [str(full_script_path)] + args
        
        # Execute script
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=SCRIPT_TIMEOUT_SECONDS
            )
            
            # Truncate output if needed
            stdout = result.stdout
            if len(stdout) > MAX_OUTPUT_SIZE:
                stdout = stdout[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            
            stderr = result.stderr
            if len(stderr) > MAX_OUTPUT_SIZE:
                stderr = stderr[:MAX_OUTPUT_SIZE] + "\n... (output truncated)"
            
            return ScriptResult(result.returncode, stdout, stderr)
        
        except subprocess.TimeoutExpired:
            raise ScriptExecutionError(
                f"Script execution timed out ({SCRIPT_TIMEOUT_SECONDS} seconds)"
            )
        except Exception as e:
            raise ScriptExecutionError(f"Failed to execute script: {str(e)}")
