"""Unified skill CRUD tool for MCP server."""

from mcp import types

from skill_mcp.core.exceptions import (
    InvalidTemplateError,
    SkillAlreadyExistsError,
    SkillNotFoundError,
)
from skill_mcp.models_crud import SkillCrudInput
from skill_mcp.services.skill_service import SkillService
from skill_mcp.services.template_service import TemplateRegistry


class SkillCrud:
    """Unified tool for skill CRUD operations."""

    @staticmethod
    def get_tool_definition() -> list[types.Tool]:
        """Get tool definition."""
        return [
            types.Tool(
                name="skill_crud",
                description="""Unified CRUD tool for skill management.

**Operations:**
- **create**: Create a new skill with templates (basic, python, bash, nodejs)
- **list**: List all skills with optional search (supports text and regex)
- **search**: Search for skills by pattern (text or regex)
- **get**: Get detailed information about a specific skill
- **validate**: Validate skill structure and get diagnostics
- **delete**: Delete a skill directory (requires confirm=true)
- **list_templates**: List all available skill templates with descriptions

**Examples:**
```json
// List available templates
{"operation": "list_templates"}

// Create a Python skill
{"operation": "create", "skill_name": "my-skill", "description": "My skill", "template": "python"}

// List all skills
{"operation": "list"}

// Search skills by text
{"operation": "search", "search": "weather"}

// Search skills by regex pattern
{"operation": "search", "search": "^api-"}

// Get skill details
{"operation": "get", "skill_name": "my-skill", "include_content": true}

// Validate skill
{"operation": "validate", "skill_name": "my-skill"}

// Delete skill
{"operation": "delete", "skill_name": "my-skill", "confirm": true}
```""",
                inputSchema=SkillCrudInput.model_json_schema(),
            )
        ]

    @staticmethod
    async def skill_crud(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle skill CRUD operations."""
        operation = input_data.operation

        try:
            if operation == "list":
                return await SkillCrud._handle_list(input_data)
            elif operation == "search":
                return await SkillCrud._handle_search(input_data)
            elif operation == "get":
                return await SkillCrud._handle_get(input_data)
            elif operation == "validate":
                return await SkillCrud._handle_validate(input_data)
            elif operation == "delete":
                return await SkillCrud._handle_delete(input_data)
            elif operation == "create":
                return await SkillCrud._handle_create(input_data)
            elif operation == "list_templates":
                return await SkillCrud._handle_list_templates(input_data)
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Unknown operation: {operation}. Valid operations: create, list, search, get, validate, delete, list_templates",
                    )
                ]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    @staticmethod
    async def _handle_list(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle list operation."""
        all_skills = SkillService.list_skills()

        # Apply search filter if provided
        skills = all_skills
        if input_data.search:
            import re

            skills = [
                s
                for s in all_skills
                if (
                    input_data.search.lower() in s.name.lower()
                    or input_data.search.lower() in (s.description or "").lower()
                    or (
                        re.search(input_data.search, s.name, re.IGNORECASE)
                        if input_data.search.startswith("^") or "*" in input_data.search
                        else False
                    )
                )
            ]

        if not skills:
            result = "No skills found in ~/.skill-mcp/skills"
            if input_data.search:
                result += f" matching '{input_data.search}'"
        else:
            result = f"Found {len(skills)} skill(s)"
            if input_data.search:
                result += f" matching '{input_data.search}'"
            result += ":\n\n"

            for skill in skills:
                status = "✓" if skill.has_skill_md else "✗"
                result += f"{status} {skill.name}\n"
                if skill.description:
                    result += f"   Description: {skill.description}\n"
                result += f"   Path: {skill.path}\n\n"

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_search(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle search operation."""
        if not input_data.search:
            return [
                types.TextContent(
                    type="text", text="Error: search pattern is required for 'search' operation"
                )
            ]

        all_skills = SkillService.list_skills()

        # Apply search filter
        import re

        skills = [
            s
            for s in all_skills
            if (
                input_data.search.lower() in s.name.lower()
                or input_data.search.lower() in (s.description or "").lower()
                or (
                    re.search(input_data.search, s.name, re.IGNORECASE)
                    if input_data.search.startswith("^") or "*" in input_data.search
                    else False
                )
            )
        ]

        if not skills:
            result = f"No skills found matching '{input_data.search}'"
        else:
            result = f"Found {len(skills)} skill(s) matching '{input_data.search}':\n\n"

            for skill in skills:
                status = "✓" if skill.has_skill_md else "✗"
                result += f"{status} {skill.name}\n"
                if skill.description:
                    result += f"   Description: {skill.description}\n"
                result += f"   Path: {skill.path}\n\n"

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_get(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle get operation."""
        if not input_data.skill_name:
            return [
                types.TextContent(
                    type="text", text="Error: skill_name is required for 'get' operation"
                )
            ]

        details = SkillService.get_skill_details(input_data.skill_name)

        result = f"Skill: {details.name}\n"
        result += f"Description: {details.description or 'N/A'}\n\n"

        # SKILL.md content
        if input_data.include_content and details.skill_md_content:
            result += "=== SKILL.md Content ===\n"
            result += details.skill_md_content
            result += "\n\n"

        # Files
        result += f"Files ({len(details.files)}):\n"
        for file in details.files:
            # Format modification time
            modified_str = ""
            if file.modified:
                from datetime import datetime

                modified_dt = datetime.fromtimestamp(file.modified)
                modified_str = f", modified: {modified_dt.strftime('%Y-%m-%d')}"

            result += f"  - {file.path} ({file.size} bytes{modified_str})"
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
        result += "\nEnvironment Variables:\n"
        if details.env_vars:
            for var in details.env_vars:
                result += f"  - {var}\n"
        else:
            result += "  (none)\n"

        result += f"\n.env file exists: {'Yes' if details.has_env_file else 'No'}\n"

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_validate(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle validate operation."""
        if not input_data.skill_name:
            return [
                types.TextContent(
                    type="text", text="Error: skill_name is required for 'validate' operation"
                )
            ]

        # Simple validation: check if skill exists and has SKILL.md
        from skill_mcp.core.config import SKILL_METADATA_FILE, SKILLS_DIR

        skill_dir = SKILLS_DIR / input_data.skill_name
        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{input_data.skill_name}' does not exist")

        errors: list[str] = []
        warnings: list[str] = []

        # Check for SKILL.md
        skill_md = skill_dir / SKILL_METADATA_FILE
        if not skill_md.exists():
            errors.append("SKILL.md file is missing")
        else:
            # Try to parse YAML frontmatter
            try:
                from skill_mcp.utils.yaml_parser import (
                    get_skill_description,
                    parse_yaml_frontmatter,
                )

                content = skill_md.read_text()
                metadata = parse_yaml_frontmatter(content)
                if not metadata:
                    warnings.append("SKILL.md has no YAML frontmatter")
                elif not get_skill_description(metadata):
                    warnings.append("SKILL.md missing description in frontmatter")
            except Exception as e:
                errors.append(f"Invalid YAML frontmatter: {str(e)}")

        is_valid = len(errors) == 0

        result = f"Validation for skill '{input_data.skill_name}':\n"
        result += f"Status: {'✓ Valid' if is_valid else '✗ Invalid'}\n\n"

        if errors:
            result += "Errors:\n"
            for error in errors:
                result += f"  - {error}\n"

        if warnings:
            result += "\nWarnings:\n"
            for warning in warnings:
                result += f"  - {warning}\n"

        if is_valid:
            result += "\nSkill is valid and ready to use."

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_delete(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle delete operation."""
        if not input_data.skill_name:
            return [
                types.TextContent(
                    type="text", text="Error: skill_name is required for 'delete' operation"
                )
            ]

        if not input_data.confirm:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: confirm=true is required to delete skill '{input_data.skill_name}'",
                )
            ]

        # Delete skill directory
        import shutil

        from skill_mcp.core.config import SKILLS_DIR

        skill_dir = SKILLS_DIR / input_data.skill_name
        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{input_data.skill_name}' does not exist")

        shutil.rmtree(skill_dir)

        return [
            types.TextContent(
                type="text", text=f"Successfully deleted skill '{input_data.skill_name}'"
            )
        ]

    @staticmethod
    async def _handle_list_templates(
        input_data: SkillCrudInput,
    ) -> list[types.TextContent]:
        """Handle list_templates operation."""
        templates = TemplateRegistry.list_templates()

        result = f"Available templates ({len(templates)}):\n\n"

        for name, spec in templates.items():
            result += f"**{name}**\n"
            result += f"  Description: {spec.description}\n"
            result += f"  Files: {', '.join(spec.files)}\n\n"

        result += "Use template name in 'create' operation:\n"
        result += '  {"operation": "create", "skill_name": "my-skill", "template": "python"}'

        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_create(input_data: SkillCrudInput) -> list[types.TextContent]:
        """Handle create operation."""
        if not input_data.skill_name:
            return [
                types.TextContent(
                    type="text", text="Error: skill_name is required for 'create' operation"
                )
            ]

        # Validate template
        template = input_data.template or "basic"
        try:
            TemplateRegistry.validate_template(template)
        except InvalidTemplateError as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        # Create skill directory with SKILL.md
        from skill_mcp.core.config import SKILL_METADATA_FILE, SKILLS_DIR

        skill_dir = SKILLS_DIR / input_data.skill_name
        if skill_dir.exists():
            raise SkillAlreadyExistsError(f"Skill '{input_data.skill_name}' already exists")

        skill_dir.mkdir(parents=True)

        # Create SKILL.md with YAML frontmatter
        description = input_data.description or f"{input_data.skill_name} skill"
        skill_md_content = f"""---
name: {input_data.skill_name}
description: {description}
---

# {input_data.skill_name}

{description}
"""

        skill_md_path = skill_dir / SKILL_METADATA_FILE
        skill_md_path.write_text(skill_md_content)

        files_created = ["SKILL.md"]

        # Add template-specific files
        if input_data.template == "python":
            script_path = skill_dir / "main.py"
            script_path.write_text(
                """#!/usr/bin/env python3
'''Main script for {skill_name}.'''

def main():
    print("Hello from {skill_name}!")

if __name__ == "__main__":
    main()
""".format(skill_name=input_data.skill_name)
            )
            files_created.append("main.py")

        elif input_data.template == "bash":
            script_path = skill_dir / "main.sh"
            script_path.write_text(
                """#!/usr/bin/env bash
# Main script for {skill_name}

echo "Hello from {skill_name}!"
""".format(skill_name=input_data.skill_name)
            )
            script_path.chmod(0o755)
            files_created.append("main.sh")

        elif input_data.template == "nodejs":
            script_path = skill_dir / "main.js"
            script_path.write_text(
                """#!/usr/bin/env node
// Main script for {skill_name}

console.log("Hello from {skill_name}!");
""".format(skill_name=input_data.skill_name)
            )
            files_created.append("main.js")

            # Create package.json
            package_json_path = skill_dir / "package.json"
            package_json_content = """{{
  "name": "{skill_name}",
  "version": "1.0.0",
  "description": "{description}",
  "main": "main.js",
  "scripts": {{
    "start": "node main.js"
  }},
  "dependencies": {{}}
}}
""".format(skill_name=input_data.skill_name, description=description)
            package_json_path.write_text(package_json_content)
            files_created.append("package.json")

        return [
            types.TextContent(
                type="text",
                text=f"Successfully created skill '{input_data.skill_name}' with {len(files_created)} files:\n"
                + "\n".join(f"  - {f}" for f in files_created),
            )
        ]
