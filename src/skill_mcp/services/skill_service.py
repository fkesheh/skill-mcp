"""Skill management service."""

from pathlib import Path
from skill_mcp.core.config import SKILLS_DIR, SKILL_METADATA_FILE
from skill_mcp.core.exceptions import SkillNotFoundError
from skill_mcp.utils.yaml_parser import parse_yaml_frontmatter, get_skill_description, get_skill_name
from skill_mcp.utils.script_detector import get_file_type, is_executable_script, has_uv_dependencies, list_executable_scripts
from skill_mcp.models import SkillSummary, SkillDetails, SkillMetadata, FileInfo, ScriptInfo
from skill_mcp.services.file_service import FileService
from skill_mcp.services.env_service import EnvironmentService


class SkillService:
    """Service for managing skills."""
    
    @staticmethod
    def list_skills() -> list[SkillSummary]:
        """
        List all available skills with descriptions.
        
        Returns:
            List of SkillSummary objects
        """
        skills = []
        
        if not SKILLS_DIR.exists():
            return skills
        
        for item in sorted(SKILLS_DIR.iterdir()):
            if item.is_dir():
                skill_summary = SkillService._get_skill_summary(item.name)
                if skill_summary:
                    skills.append(skill_summary)
        
        return skills
    
    @staticmethod
    def _get_skill_summary(skill_name: str) -> SkillSummary | None:
        """Get a summary of a single skill."""
        skill_dir = SKILLS_DIR / skill_name
        
        if not skill_dir.is_dir():
            return None
        
        skill_md_path = skill_dir / SKILL_METADATA_FILE
        has_skill_md = skill_md_path.exists()
        
        description = ""
        if has_skill_md:
            try:
                content = skill_md_path.read_text()
                metadata = parse_yaml_frontmatter(content)
                description = get_skill_description(metadata)
            except Exception:
                pass
        
        return SkillSummary(
            name=skill_name,
            description=description,
            path=str(skill_dir),
            has_skill_md=has_skill_md
        )
    
    @staticmethod
    def get_skill_details(skill_name: str) -> SkillDetails:
        """
        Get comprehensive information about a skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            SkillDetails object
            
        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill_dir = SKILLS_DIR / skill_name
        
        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{skill_name}' does not exist")
        
        # Get metadata from SKILL.md
        metadata = SkillMetadata()
        description = ""
        skill_md_content = None
        skill_md_path = skill_dir / SKILL_METADATA_FILE
        
        if skill_md_path.exists():
            try:
                content = skill_md_path.read_text()
                skill_md_content = content  # Store the full content
                parsed = parse_yaml_frontmatter(content)
                if parsed:
                    metadata.name = get_skill_name(parsed)
                    metadata.description = get_skill_description(parsed)
                    metadata.extra = {k: v for k, v in parsed.items() 
                                    if k not in ("name", "description")}
                    description = metadata.description or ""
            except Exception:
                pass
        
        # List all files
        files_list = FileService.list_skill_files(skill_name)
        files = []
        scripts = []
        
        for file_info in files_list:
            file_path = skill_dir / file_info["path"]
            file_type = get_file_type(file_path)
            is_exec = is_executable_script(file_path)
            
            has_uv_deps = None
            if file_type == "python" and is_exec:
                has_uv_deps = has_uv_dependencies(file_path)
            
            file_obj = FileInfo(
                path=file_info["path"],
                size=file_info["size"],
                type=file_type,
                is_executable=is_exec,
                has_uv_deps=has_uv_deps
            )
            files.append(file_obj)
            
            # Collect executable scripts
            if is_exec:
                scripts.append(ScriptInfo(
                    path=file_info["path"],
                    type=file_type,
                    has_uv_deps=has_uv_deps or False
                ))
        
        # Get environment variables
        env_vars = []
        try:
            env_vars = EnvironmentService.get_env_keys(skill_name)
        except Exception:
            pass
        
        has_env_file = (skill_dir / ".env").exists()
        
        return SkillDetails(
            name=skill_name,
            description=description,
            metadata=metadata,
            files=files,
            scripts=scripts,
            env_vars=env_vars,
            has_env_file=has_env_file,
            skill_md_content=skill_md_content
        )
