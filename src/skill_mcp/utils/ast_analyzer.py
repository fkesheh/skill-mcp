"""AST analyzer for extracting imports and dependencies from Python files."""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set

# Standard library modules (Python 3.10+)
STDLIB_MODULES = set(sys.stdlib_module_names)


class PythonImportAnalyzer:
    """Analyze Python files to extract imports, function calls, and env var usage."""

    @staticmethod
    def extract_imports(file_path: Path) -> Dict[str, List[str]]:
        """
        Extract all imports from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary with categorized imports:
            {
                'standard_lib': ['os', 'sys', 'json'],
                'third_party': ['requests', 'pandas'],
                'local': ['utils', 'helpers.math_utils'],
                'cross_skill': []  # Detected via skill_references pattern
            }
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            imports = {
                "standard_lib": [],
                "third_party": [],
                "local": [],
                "cross_skill": [],
            }

            for node in ast.walk(tree):
                # Handle "import x" statements
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        imports = PythonImportAnalyzer._categorize_import(
                            module_name, imports, file_path
                        )

                # Handle "from x import y" statements
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        imports = PythonImportAnalyzer._categorize_import(
                            module_name, imports, file_path
                        )

            return imports

        except Exception:
            # If we can't parse the file, return empty imports
            return {
                "standard_lib": [],
                "third_party": [],
                "local": [],
                "cross_skill": [],
            }

    @staticmethod
    def _categorize_import(
        module_name: str, imports: Dict[str, List[str]], file_path: Path
    ) -> Dict[str, List[str]]:
        """Categorize an import as standard lib, third party, or local."""
        if module_name in STDLIB_MODULES:
            if module_name not in imports["standard_lib"]:
                imports["standard_lib"].append(module_name)
        else:
            # Check if it's a local import (file exists in same directory or parent)
            parent_dir = file_path.parent
            potential_local = parent_dir / f"{module_name}.py"
            potential_local_dir = parent_dir / module_name

            if potential_local.exists() or potential_local_dir.exists():
                if module_name not in imports["local"]:
                    imports["local"].append(module_name)
            else:
                # Assume it's third-party
                if module_name not in imports["third_party"]:
                    imports["third_party"].append(module_name)

        return imports

    @staticmethod
    def extract_function_calls(file_path: Path) -> List[str]:
        """
        Extract all function calls from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of function names called in the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            function_calls = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = PythonImportAnalyzer._get_func_name(node.func)
                    if func_name and func_name not in function_calls:
                        function_calls.append(func_name)

            return function_calls

        except Exception:
            return []

    @staticmethod
    def _get_func_name(node: ast.expr) -> str:
        """Extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle chained attributes like obj.method()
            value = PythonImportAnalyzer._get_func_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        return ""

    @staticmethod
    def extract_env_var_usage(file_path: Path) -> Set[str]:
        """
        Find environment variable usage (os.environ, os.getenv).

        Args:
            file_path: Path to the Python file

        Returns:
            Set of environment variable names used in the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            env_vars: Set[str] = set()

            for node in ast.walk(tree):
                # Handle os.environ['VAR'] or os.environ.get('VAR')
                if isinstance(node, ast.Subscript):
                    if PythonImportAnalyzer._is_environ_access(node.value):
                        var_name = PythonImportAnalyzer._extract_string_literal(node.slice)
                        if var_name:
                            env_vars.add(var_name)

                # Handle os.getenv('VAR')
                elif isinstance(node, ast.Call):
                    if PythonImportAnalyzer._is_getenv_call(node.func):
                        if node.args:
                            var_name = PythonImportAnalyzer._extract_string_literal(node.args[0])
                            if var_name:
                                env_vars.add(var_name)

            return env_vars

        except Exception:
            return set()

    @staticmethod
    def _is_environ_access(node: ast.expr) -> bool:
        """Check if node is os.environ access."""
        if isinstance(node, ast.Attribute):
            if node.attr == "environ" and isinstance(node.value, ast.Name):
                return node.value.id == "os"
        return False

    @staticmethod
    def _is_getenv_call(node: ast.expr) -> bool:
        """Check if node is os.getenv call."""
        if isinstance(node, ast.Attribute):
            if node.attr == "getenv" and isinstance(node.value, ast.Name):
                return node.value.id == "os"
        return False

    @staticmethod
    def _extract_string_literal(node: ast.expr) -> str:
        """Extract string literal from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    @staticmethod
    def get_all_defined_functions(file_path: Path) -> List[str]:
        """
        Get all function and class definitions in a file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of function/class names defined in the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            definitions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    definitions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    definitions.append(node.name)

            return definitions

        except Exception:
            return []
