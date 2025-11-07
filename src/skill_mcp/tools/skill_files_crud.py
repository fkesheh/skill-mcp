"""Unified file CRUD tool for MCP server."""

from mcp import types

from skill_mcp.models_crud import SkillFilesCrudInput
from skill_mcp.services.file_service import FileService


class SkillFilesCrud:
    """Unified tool for skill file CRUD operations."""

    @staticmethod
    def get_tool_definition() -> list[types.Tool]:
        """Get tool definition."""
        return [
            types.Tool(
                name="skill_files_crud",
                description="""Unified CRUD tool for skill file operations. Supports both single and bulk operations.

**Operations:**
- **read**: Read a file's content
- **create**: Create one or more files (supports atomic mode for bulk)
- **update**: Update one or more files
- **delete**: Delete a file (SKILL.md is protected and cannot be deleted)

**Single File Examples:**
```json
// Read a file
{"operation": "read", "skill_name": "my-skill", "file_path": "script.py"}

// Create a single file
{"operation": "create", "skill_name": "my-skill", "file_path": "new.py", "content": "print('hello')"}

// Update a single file
{"operation": "update", "skill_name": "my-skill", "file_path": "script.py", "content": "print('updated')"}

// Delete a file
{"operation": "delete", "skill_name": "my-skill", "file_path": "old.py"}
```

**Bulk File Examples:**
```json
// Create multiple files atomically (all-or-nothing)
{
  "operation": "create",
  "skill_name": "my-skill",
  "files": [
    {"path": "src/main.py", "content": "# Main"},
    {"path": "src/utils.py", "content": "# Utils"},
    {"path": "README.md", "content": "# Docs"}
  ],
  "atomic": true
}

// Update multiple files
{
  "operation": "update",
  "skill_name": "my-skill",
  "files": [
    {"path": "file1.py", "content": "new content 1"},
    {"path": "file2.py", "content": "new content 2"}
  ]
}
```""",
                inputSchema=SkillFilesCrudInput.model_json_schema(),
            )
        ]

    @staticmethod
    async def skill_files_crud(input_data: SkillFilesCrudInput) -> list[types.TextContent]:
        """Handle file CRUD operations."""
        operation = input_data.operation

        try:
            if operation == "read":
                return await SkillFilesCrud._handle_read(input_data)
            elif operation == "create":
                return await SkillFilesCrud._handle_create(input_data)
            elif operation == "update":
                return await SkillFilesCrud._handle_update(input_data)
            elif operation == "delete":
                return await SkillFilesCrud._handle_delete(input_data)
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Unknown operation: {operation}. Valid operations: read, create, update, delete",
                    )
                ]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    @staticmethod
    async def _handle_read(input_data: SkillFilesCrudInput) -> list[types.TextContent]:
        """Handle read operation."""
        if not input_data.file_path:
            return [
                types.TextContent(
                    type="text", text="Error: file_path is required for 'read' operation"
                )
            ]

        content = FileService.read_file(input_data.skill_name, input_data.file_path)

        result = f"=== {input_data.file_path} ===\n{content}"
        return [types.TextContent(type="text", text=result)]

    @staticmethod
    async def _handle_create(input_data: SkillFilesCrudInput) -> list[types.TextContent]:
        """Handle create operation (single or bulk)."""
        # Bulk operation
        if input_data.files:
            if input_data.file_path or input_data.content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Cannot specify both 'files' (bulk) and 'file_path'/'content' (single) parameters",
                    )
                ]

            # Manually implement bulk creation with atomicity
            created_files = []
            try:
                for file_spec in input_data.files:
                    FileService.create_file(
                        input_data.skill_name, file_spec.path, file_spec.content
                    )
                    created_files.append(file_spec.path)

                return [
                    types.TextContent(
                        type="text",
                        text=f"Successfully created {len(created_files)} files:\n"
                        + "\n".join(f"  - {f}" for f in created_files),
                    )
                ]
            except Exception as e:
                # Rollback on error if atomic mode
                if input_data.atomic:
                    from skill_mcp.core.config import SKILLS_DIR

                    skill_dir = SKILLS_DIR / input_data.skill_name
                    for created_path in created_files:
                        try:
                            (skill_dir / created_path).unlink()
                        except Exception:
                            pass
                raise e

        # Single operation
        if not input_data.file_path or not input_data.content:
            return [
                types.TextContent(
                    type="text",
                    text="Error: file_path and content are required for single file create",
                )
            ]

        FileService.create_file(input_data.skill_name, input_data.file_path, input_data.content)

        return [
            types.TextContent(
                type="text",
                text=f"Successfully created file '{input_data.file_path}' ({len(input_data.content)} characters)",
            )
        ]

    @staticmethod
    async def _handle_update(input_data: SkillFilesCrudInput) -> list[types.TextContent]:
        """Handle update operation (single or bulk)."""
        # Bulk operation
        if input_data.files:
            if input_data.file_path or input_data.content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Cannot specify both 'files' (bulk) and 'file_path'/'content' (single) parameters",
                    )
                ]

            updated_count = 0
            for file_spec in input_data.files:
                FileService.update_file(input_data.skill_name, file_spec.path, file_spec.content)
                updated_count += 1

            return [
                types.TextContent(type="text", text=f"Successfully updated {updated_count} files")
            ]

        # Single operation
        if not input_data.file_path or not input_data.content:
            return [
                types.TextContent(
                    type="text",
                    text="Error: file_path and content are required for single file update",
                )
            ]

        FileService.update_file(input_data.skill_name, input_data.file_path, input_data.content)

        return [
            types.TextContent(
                type="text",
                text=f"Successfully updated file '{input_data.file_path}' ({len(input_data.content)} characters)",
            )
        ]

    @staticmethod
    async def _handle_delete(input_data: SkillFilesCrudInput) -> list[types.TextContent]:
        """Handle delete operation."""
        if not input_data.file_path:
            return [
                types.TextContent(
                    type="text", text="Error: file_path is required for 'delete' operation"
                )
            ]

        FileService.delete_file(input_data.skill_name, input_data.file_path)

        return [
            types.TextContent(
                type="text", text=f"Successfully deleted file '{input_data.file_path}'"
            )
        ]
