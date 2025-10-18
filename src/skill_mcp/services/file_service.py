"""File management service."""

from pathlib import Path
from typing import List, Dict, Any
from skill_mcp.core.config import SKILLS_DIR, MAX_FILE_SIZE, SKILL_METADATA_FILE
from skill_mcp.core.exceptions import SkillNotFoundError, FileNotFoundError, FileTooBigError, InvalidPathError
from skill_mcp.utils.path_utils import validate_path


class FileService:
    """Service for managing skill files."""
    
    @staticmethod
    def list_skill_files(skill_name: str) -> List[Dict[str, Any]]:
        """
        List all files in a skill directory recursively.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            List of file information dictionaries
            
        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill_dir = SKILLS_DIR / skill_name
        
        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")
        
        if not skill_dir.is_dir():
            raise SkillNotFoundError(f"'{skill_name}' is not a directory")
        
        files = []
        for item in sorted(skill_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(skill_dir)
                files.append({
                    "path": str(rel_path),
                    "size": item.stat().st_size,
                    "type": "file"
                })
        
        return files
    
    @staticmethod
    def read_file(skill_name: str, file_path: str) -> str:
        """
        Read content of a skill file.
        
        Args:
            skill_name: Name of the skill
            file_path: Relative path to the file
            
        Returns:
            File content as string
            
        Raises:
            InvalidPathError: If path is invalid
            FileNotFoundError: If file doesn't exist
            FileTooBigError: If file exceeds size limit
        """
        full_path = validate_path(skill_name, file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(
                f"File '{file_path}' does not exist in skill '{skill_name}'"
            )
        
        if not full_path.is_file():
            raise FileNotFoundError(f"'{file_path}' is not a file")
        
        file_size = full_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise FileTooBigError(
                f"File too large ({file_size / 1024:.1f} KB). "
                f"Maximum size is {MAX_FILE_SIZE / 1024:.1f} KB."
            )
        
        return full_path.read_text()
    
    @staticmethod
    def create_file(skill_name: str, file_path: str, content: str) -> None:
        """
        Create a new skill file.
        
        Args:
            skill_name: Name of the skill
            file_path: Relative path for the new file
            content: File content
            
        Raises:
            InvalidPathError: If path is invalid
            FileNotFoundError: If file already exists
        """
        full_path = validate_path(skill_name, file_path)
        
        if full_path.exists():
            raise FileNotFoundError(
                f"File '{file_path}' already exists in skill '{skill_name}'. "
                "Use update to modify it."
            )
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        full_path.write_text(content)
    
    @staticmethod
    def update_file(skill_name: str, file_path: str, content: str) -> None:
        """
        Update an existing skill file.
        
        Args:
            skill_name: Name of the skill
            file_path: Relative path to the file
            content: New file content
            
        Raises:
            InvalidPathError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        full_path = validate_path(skill_name, file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(
                f"File '{file_path}' does not exist in skill '{skill_name}'. "
                "Use create to create it."
            )
        
        if not full_path.is_file():
            raise FileNotFoundError(f"'{file_path}' is not a file")
        
        full_path.write_text(content)
    
    @staticmethod
    def delete_file(skill_name: str, file_path: str) -> None:
        """
        Delete a skill file.
        
        Args:
            skill_name: Name of the skill
            file_path: Relative path to the file
            
        Raises:
            InvalidPathError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        full_path = validate_path(skill_name, file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(
                f"File '{file_path}' does not exist in skill '{skill_name}'"
            )
        
        if not full_path.is_file():
            raise FileNotFoundError(
                f"'{file_path}' is not a file. Cannot delete directories."
            )
        
        full_path.unlink()
