"""Environment variable management service."""

from pathlib import Path
from typing import Dict

from dotenv import dotenv_values

from skill_mcp.core.config import ENV_FILE_NAME, SKILLS_DIR
from skill_mcp.core.exceptions import EnvFileError, SkillNotFoundError


class EnvironmentService:
    """Service for managing skill-specific environment variables."""

    @staticmethod
    def get_env_file_path(skill_name: str) -> Path:
        """Get path to .env file for a skill."""
        skill_dir = SKILLS_DIR / skill_name
        return skill_dir / ENV_FILE_NAME

    @staticmethod
    def load_skill_env(skill_name: str) -> Dict[str, str]:
        """
        Load environment variables from skill's .env file.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary of environment variables

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be read
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        env_file = EnvironmentService.get_env_file_path(skill_name)

        try:
            if env_file.exists():
                # Filter out None values from dotenv_values
                values = dotenv_values(env_file)
                return {k: v for k, v in values.items() if v is not None}
            return {}
        except Exception as e:
            raise EnvFileError(f"Failed to load .env for skill '{skill_name}': {str(e)}")

    @staticmethod
    def read_env_file(skill_name: str) -> str:
        """
        Read raw .env file contents (allows LLM to see and edit).

        Args:
            skill_name: Name of the skill

        Returns:
            Raw .env file content as string

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be read
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        env_file = EnvironmentService.get_env_file_path(skill_name)

        try:
            if env_file.exists():
                return env_file.read_text()
            return ""
        except Exception as e:
            raise EnvFileError(f"Failed to read .env for skill '{skill_name}': {str(e)}")

    @staticmethod
    def update_env_file(skill_name: str, content: str) -> None:
        """
        Update skill's .env file with new content.

        Args:
            skill_name: Name of the skill
            content: New .env file content

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be written
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        env_file = EnvironmentService.get_env_file_path(skill_name)

        try:
            env_file.write_text(content)
        except Exception as e:
            raise EnvFileError(f"Failed to write .env for skill '{skill_name}': {str(e)}")

    @staticmethod
    def get_env_keys(skill_name: str) -> list[str]:
        """
        Get list of environment variable names for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of environment variable names

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        env = EnvironmentService.load_skill_env(skill_name)
        return sorted(env.keys())

    @staticmethod
    def set_variables(skill_name: str, variables: Dict[str, str]) -> None:
        """
        Set environment variables in skill's .env file.
        Always merges with existing variables.

        Args:
            skill_name: Name of the skill
            variables: Dictionary of key-value pairs to set

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be written
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        # Load existing vars and merge
        existing_vars = EnvironmentService.load_skill_env(skill_name)
        existing_vars.update(variables)

        # Write back
        content = "\n".join(f"{key}={value}" for key, value in existing_vars.items())
        EnvironmentService.update_env_file(skill_name, content)

    @staticmethod
    def delete_variables(skill_name: str, keys: list[str]) -> int:
        """
        Delete specific environment variables from skill's .env file.

        Args:
            skill_name: Name of the skill
            keys: List of variable names to delete

        Returns:
            Number of variables actually deleted

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be written
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        # Load existing vars
        existing_vars = EnvironmentService.load_skill_env(skill_name)

        # Track how many were actually deleted
        deleted_count = 0

        # Remove specified keys
        for key in keys:
            if key in existing_vars:
                existing_vars.pop(key)
                deleted_count += 1

        # Write back
        if existing_vars:
            content = "\n".join(f"{key}={value}" for key, value in existing_vars.items())
            EnvironmentService.update_env_file(skill_name, content)
        else:
            # Clear the file if no vars left
            EnvironmentService.update_env_file(skill_name, "")

        return deleted_count

    @staticmethod
    def clear_env(skill_name: str) -> None:
        """
        Clear all environment variables from skill's .env file.

        Args:
            skill_name: Name of the skill

        Raises:
            SkillNotFoundError: If skill doesn't exist
            EnvFileError: If .env file can't be written
        """
        skill_dir = SKILLS_DIR / skill_name

        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")

        EnvironmentService.update_env_file(skill_name, "")
