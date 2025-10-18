"""Script detection and analysis utilities."""

from pathlib import Path
from typing import Literal


def get_file_type(file_path: Path) -> str:
    """
    Determine the file type based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File type string (e.g., 'python', 'shell', 'markdown', 'unknown')
    """
    suffix = file_path.suffix.lower()
    
    type_map = {
        ".py": "python",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "text",
        ".env": "env",
    }
    
    return type_map.get(suffix, "unknown")


def is_executable_script(file_path: Path) -> bool:
    """
    Detect if file is an executable script.
    
    Checks:
    - Known executable extensions (.py, .sh, .bash, etc.)
    - Shebang line (#!/...)
    - Executable permission
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is an executable script
    """
    file_type = get_file_type(file_path)
    
    # Known executable types
    if file_type in ("python", "shell"):
        return True
    
    # Check for shebang
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
            if first_line.startswith("#!"):
                return True
    except Exception:
        pass
    
    # Check executable permission on Unix-like systems
    try:
        import os
        return os.access(file_path, os.X_OK)
    except Exception:
        pass
    
    return False


def has_uv_dependencies(script_path: Path) -> bool:
    """
    Check if Python script has uv inline metadata (PEP 723).
    
    Looks for:
    # /// script
    # dependencies = [...]
    # ///
    
    Args:
        script_path: Path to the script
        
    Returns:
        True if script has uv metadata
    """
    if script_path.suffix.lower() != ".py":
        return False
    
    try:
        content = script_path.read_text(encoding="utf-8", errors="ignore")
        return "# /// script" in content or "# /// pyproject" in content
    except Exception:
        return False


def list_executable_scripts(directory: Path) -> list[Path]:
    """
    Find all executable scripts in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of paths to executable scripts
    """
    if not directory.exists():
        return []
    
    scripts = []
    for file_path in directory.rglob("*"):
        if file_path.is_file() and is_executable_script(file_path):
            scripts.append(file_path)
    
    return sorted(scripts)
