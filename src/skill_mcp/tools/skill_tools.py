"""Skill management tools for MCP server."""

from mcp import types
from skill_mcp.models import ListSkillsInput, GetSkillDetailsInput
from skill_mcp.services.skill_service import SkillService
from skill_mcp.core.exceptions import SkillNotFoundError


class SkillTools:
    """Tools for skill management."""
    
    @staticmethod
    def get_list_tools() -> list[types.Tool]:
        """Get skill listing tools."""
        return [
            types.Tool(
                name="list_skills",
                description="""List all available skills in the ~/.skill-mcp/skills directory with their descriptions parsed from SKILL.md frontmatter.

This tool returns a lightweight overview of all installed skills, including:
- Skill name and directory path
- Description extracted from SKILL.md YAML frontmatter
- Validation status (whether SKILL.md exists)

Use this tool first to discover what skills are available before working with specific skills. Each skill is a self-contained directory that may contain scripts, data files, and a SKILL.md metadata file.

Returns: List of all available skills with names, paths, and descriptions.""",
                inputSchema=ListSkillsInput.model_json_schema(),
            ),
            types.Tool(
                name="get_skill_details",
                description="""Get comprehensive details about a specific skill including all files, executable scripts, environment variables, and metadata from SKILL.md.

This tool provides complete information about a skill:
- Full SKILL.md content (documentation and metadata)
- All files in the skill directory with file type and size
- Executable scripts with their locations
- Whether Python scripts have PEP 723 inline dependencies (uv metadata)
- Environment variables defined in the skill's .env file
- Whether a .env file exists for this skill

Use this tool to:
1. Understand what a skill does (SKILL.md content)
2. See what files and scripts are available
3. Check what environment variables are configured
4. Determine which scripts can be executed and what dependencies they have

Required parameter: skill_name (the name of the skill directory)

Returns: Complete skill details including files, scripts, environment variables, and SKILL.md documentation.""",
                inputSchema=GetSkillDetailsInput.model_json_schema(),
            ),
        ]
    
    @staticmethod
    async def list_skills() -> list[types.TextContent]:
        """List all available skills."""
        try:
            skills = SkillService.list_skills()
            
            if not skills:
                result = "No skills found in ~/.skill-mcp/skills"
            else:
                result = f"Found {len(skills)} skill(s):\n\n"
                for skill in skills:
                    status = "✓" if skill.has_skill_md else "✗"
                    result += f"{status} {skill.name}\n"
                    if skill.description:
                        result += f"   Description: {skill.description}\n"
                    result += f"   Path: {skill.path}\n\n"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error listing skills: {str(e)}")]
    
    @staticmethod
    async def get_skill_details(input_data: GetSkillDetailsInput) -> list[types.TextContent]:
        """Get detailed information about a skill."""
        try:
            details = SkillService.get_skill_details(input_data.skill_name)
            
            result = f"Skill: {details.name}\n"
            result += f"Description: {details.description or 'N/A'}\n\n"
            
            # SKILL.md content
            if details.skill_md_content:
                result += "=== SKILL.md Content ===\n"
                result += details.skill_md_content
                result += "\n\n"
            
            # Files
            result += f"Files ({len(details.files)}):\n"
            for file in details.files:
                result += f"  - {file.path} ({file.size} bytes, type: {file.type})"
                if file.is_executable:
                    result += " [executable]"
                    if file.has_uv_deps is not None:
                        result += f" [uv deps: {'yes' if file.has_uv_deps else 'no'}]"
                result += "\n"
            
            # Scripts
            if details.scripts:
                result += f"\nScripts ({len(details.scripts)}):\n"
                for script in details.scripts:
                    result += f"  - {script.path} ({script.type})"
                    if script.has_uv_deps:
                        result += " [has uv dependencies]"
                    result += "\n"
            
            # Environment variables
            result += f"\nEnvironment Variables:\n"
            if details.env_vars:
                for var in details.env_vars:
                    result += f"  - {var}\n"
            else:
                result += "  (none)\n"
            
            result += f"\n.env file exists: {'Yes' if details.has_env_file else 'No'}\n"
            
            return [types.TextContent(type="text", text=result)]
        except SkillNotFoundError as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting skill details: {str(e)}")]
