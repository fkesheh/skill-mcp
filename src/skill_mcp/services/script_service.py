"""Script execution service."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_mcp.core.config import (
    DEFAULT_PYTHON_INTERPRETER,
    MAX_OUTPUT_SIZE,
    SCRIPT_TIMEOUT_SECONDS,
    SKILLS_DIR,
)
from skill_mcp.core.exceptions import InvalidPathError, ScriptExecutionError, SkillNotFoundError
from skill_mcp.services.env_service import EnvironmentService
from skill_mcp.utils.path_utils import validate_path
from skill_mcp.utils.script_detector import has_npm_dependencies, has_uv_dependencies


def extract_pep723_dependencies(content: str) -> List[str]:
    """
    Extract dependencies from PEP 723 metadata in code.

    Args:
        content: Python code or file content

    Returns:
        List of dependency strings (e.g., ["requests>=2.31.0", "pandas"])
    """
    # Match PEP 723 script block
    pattern = r"#\s*///\s*script\s*\n(.*?)#\s*///\s*$"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return []

    metadata_block = match.group(1)

    # Extract dependencies array
    deps_pattern = r"dependencies\s*=\s*\[(.*?)\]"
    deps_match = re.search(deps_pattern, metadata_block, re.DOTALL)

    if not deps_match:
        return []

    deps_content = deps_match.group(1)

    # Extract individual dependency strings
    dep_strings = re.findall(r'["\']([^"\']+)["\']', deps_content)

    return dep_strings


def merge_dependencies(code: str, additional_deps: List[str]) -> str:
    """
    Merge additional dependencies into code's PEP 723 metadata.

    If code has no PEP 723 block, creates one.
    If code has PEP 723 block, merges dependencies (deduplicates).

    Args:
        code: Python code (may or may not have PEP 723 metadata)
        additional_deps: List of dependencies to add

    Returns:
        Modified code with merged dependencies
    """
    if not additional_deps:
        return code

    # Extract existing dependencies
    existing_deps = extract_pep723_dependencies(code)

    # Merge and deduplicate (keep order, prefer later versions)
    # Use dict to preserve order and handle duplicates
    dep_map: Dict[str, str] = {}

    for dep in existing_deps + additional_deps:
        # Extract package name (before any version specifier)
        pkg_name = re.split(r"[<>=!]", dep)[0].strip()
        dep_map[pkg_name] = dep

    merged_deps = list(dep_map.values())

    if not merged_deps:
        return code

    # Check if code already has PEP 723 metadata
    pattern = r"#\s*///\s*script\s*\n(.*?)#\s*///\s*$"
    match = re.search(pattern, code, re.MULTILINE | re.DOTALL)

    if match:
        # Replace existing dependencies
        metadata_block = match.group(1)

        # Format new dependencies with proper newlines
        deps_lines = ["# dependencies = ["]
        for dep in merged_deps:
            deps_lines.append(f'#   "{dep}",')
        deps_lines.append("# ]")
        deps_str = "\n".join(deps_lines)

        # Replace or add dependencies in metadata block
        deps_pattern = r"#\s*dependencies\s*=\s*\[.*?#\s*\]"
        if re.search(deps_pattern, metadata_block, re.DOTALL):
            new_metadata = re.sub(deps_pattern, deps_str, metadata_block, flags=re.DOTALL)
        else:
            # Add dependencies to metadata
            new_metadata = deps_str + "\n" + metadata_block

        # Replace the entire PEP 723 block
        new_code = (
            code[: match.start()] + f"# /// script\n{new_metadata}# ///\n" + code[match.end() :]
        )
        return new_code
    else:
        # Create new PEP 723 block at the beginning
        deps_lines = ["# /// script", "# dependencies = ["]
        for dep in merged_deps:
            deps_lines.append(f'#   "{dep}",')
        deps_lines.append("# ]")
        deps_lines.append("# ///")
        deps_lines.append("")
        pep723_block = "\n".join(deps_lines)
        return pep723_block + code


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
            "success": self.exit_code == 0,
        }


class ScriptService:
    """Service for executing skill scripts."""

    @staticmethod
    async def run_script(
        skill_name: str,
        script_path: str,
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
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
        elif ext in (".js", ".mjs"):
            # Check if script has package.json
            if has_npm_dependencies(full_script_path):
                # Run npm install if node_modules doesn't exist
                node_modules = full_script_path.parent / "node_modules"
                if not node_modules.exists():
                    try:
                        subprocess.run(
                            ["npm", "install"],
                            cwd=str(full_script_path.parent),
                            env=env,
                            capture_output=True,
                            timeout=SCRIPT_TIMEOUT_SECONDS,
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        raise ScriptExecutionError(f"npm install failed: {e.stderr}")
                    except subprocess.TimeoutExpired:
                        raise ScriptExecutionError(
                            f"npm install timed out ({SCRIPT_TIMEOUT_SECONDS} seconds)"
                        )
            cmd = ["node", str(full_script_path)] + args
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
                timeout=SCRIPT_TIMEOUT_SECONDS,
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

    @staticmethod
    async def execute_python_code(
        code: str,
        skill_references: Optional[List[str]] = None,
    ) -> ScriptResult:
        """
        Execute Python code directly without requiring a script file.

        Supports PEP 723 inline dependencies using /// script comments.
        Can reference skill files using namespace format (skill_name:path/to/file.py).
        Automatically aggregates PEP 723 dependencies from referenced skill files.

        Args:
            code: Python code to execute (can include PEP 723 dependencies)
            skill_references: List of skill files in namespace format to make available
                            e.g., ["calculator:utils.py", "weather:api/client.py"]

        Returns:
            ScriptResult with stdout, stderr, and exit code

        Raises:
            ScriptExecutionError: If execution fails
        """
        temp_file = None
        try:
            # Parse skill references and collect dependencies
            env = os.environ.copy()
            python_paths: List[str] = []
            aggregated_deps: List[str] = []

            if skill_references:
                for ref in skill_references:
                    # Parse namespace format: skill_name:path/to/file.py
                    if ":" not in ref:
                        raise ScriptExecutionError(
                            f"Invalid skill reference format: '{ref}'. Expected 'skill_name:path/to/file.py'"
                        )

                    skill_name, file_path = ref.split(":", 1)
                    skill_dir = SKILLS_DIR / skill_name

                    if not skill_dir.exists():
                        raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

                    # Add skill directory to PYTHONPATH
                    if str(skill_dir) not in python_paths:
                        python_paths.append(str(skill_dir))

                    # Read the referenced file and extract its dependencies
                    ref_file_path = skill_dir / file_path
                    if ref_file_path.exists() and ref_file_path.is_file():
                        try:
                            ref_content = ref_file_path.read_text(encoding="utf-8")
                            ref_deps = extract_pep723_dependencies(ref_content)
                            aggregated_deps.extend(ref_deps)
                        except Exception:
                            # If we can't read or parse the file, just skip dependency extraction
                            pass

            # Merge aggregated dependencies into the code
            if aggregated_deps:
                code = merge_dependencies(code, aggregated_deps)

            # Create temporary Python file with merged code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                temp_file = Path(f.name)

            # Add paths to PYTHONPATH
            if python_paths:
                existing_path = env.get("PYTHONPATH", "")
                new_paths = ":".join(python_paths)
                env["PYTHONPATH"] = f"{new_paths}:{existing_path}" if existing_path else new_paths

            # Check if code has PEP 723 dependencies (same logic as has_uv_dependencies)
            has_deps = "# /// script" in code or "# /// pyproject" in code

            # Build command
            if has_deps:
                cmd = ["uv", "run", str(temp_file)]
            else:
                cmd = [DEFAULT_PYTHON_INTERPRETER, str(temp_file)]

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
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
                f"Code execution timed out ({SCRIPT_TIMEOUT_SECONDS} seconds)"
            )
        except (SkillNotFoundError, ScriptExecutionError):
            raise
        except Exception as e:
            raise ScriptExecutionError(f"Failed to execute code: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
