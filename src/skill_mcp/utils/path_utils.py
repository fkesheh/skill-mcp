"""Path validation utilities."""

from pathlib import Path
from skill_mcp.core.config import SKILLS_DIR
from skill_mcp.core.exceptions import PathTraversalError, InvalidPathError


def validate_path(skill_name: str, file_path: str) -> Path:
    """
    Validate and construct a safe path within the skill directory.
    Prevents directory traversal attacks.
    
    Args:
        skill_name: Name of the skill
        file_path: Relative path within the skill
        
    Returns:
        Validated Path object
        
    Raises:
        PathTraversalError: If path traversal is detected
        InvalidPathError: If path is invalid
    """
    # Normalize the path and check for traversal attempts
    normalized_path = Path(file_path).as_posix()
    if ".." in normalized_path or normalized_path.startswith("/"):
        raise PathTraversalError(f"Invalid path: {file_path}. Path traversal detected.")
    
    skill_dir = SKILLS_DIR / skill_name
    full_path = skill_dir / file_path
    
    # Ensure the resolved path is within the skill directory
    try:
        full_path.resolve().relative_to(skill_dir.resolve())
    except ValueError:
        raise InvalidPathError(f"Invalid path: {file_path}. Must be within skill directory.")
    
    return full_path
