"""File management tools for MCP server."""

from mcp import types
from skill_mcp.models import (
    ReadSkillFileInput,
    CreateSkillFileInput,
    UpdateSkillFileInput,
    DeleteSkillFileInput,
)
from skill_mcp.services.file_service import FileService
from skill_mcp.core.exceptions import SkillMCPException


class FileTools:
    """Tools for file management."""
    
    @staticmethod
    def get_file_tools() -> list[types.Tool]:
        """Get file management tools."""
        return [
            types.Tool(
                name="read_skill_file",
                description="""Read and display the complete content of a specific file within a skill directory.

This tool allows you to view the contents of any file in a skill. Use this to:
- Read Python scripts, data files, configuration files, etc.
- Examine file contents before modifying them
- Check file format and structure before running scripts
- View documentation or data files

Parameters:
- skill_name: The name of the skill directory (e.g., 'my-skill')
- file_path: Relative path to the file within the skill directory (e.g., 'scripts/process.py', 'data/input.csv', 'README.md')

Important: file_path is relative to the skill's root directory, not the skills directory. Use forward slashes even on Windows.

Returns: The complete file content as text. If the file is very large, it will be truncated with a message indicating truncation.""",
                inputSchema=ReadSkillFileInput.model_json_schema(),
            ),
            types.Tool(
                name="create_skill_file",
                description="""Create a new file within a skill directory. Automatically creates parent directories if they don't exist.

This tool allows you to:
- Create new Python scripts or other executable files
- Create configuration files (e.g., JSON, YAML, CSV)
- Create data files and documentation
- Build new functionality within a skill

Parameters:
- skill_name: The name of the skill directory (e.g., 'my-skill')
- file_path: Relative path for the new file (e.g., 'scripts/new_script.py', 'data/new_data.json')
- content: The complete text content to write to the file

Behavior:
- Creates parent directories automatically (e.g., if 'scripts/' doesn't exist, it will be created)
- Does not overwrite existing files (use update_skill_file to modify existing files)
- File_path must be relative to the skill's root directory
- Use forward slashes for path separators

Returns: Success message with filename and character count.""",
                inputSchema=CreateSkillFileInput.model_json_schema(),
            ),
            types.Tool(
                name="update_skill_file",
                description="""Update the content of an existing file in a skill directory.

This tool allows you to:
- Modify existing Python scripts or other files
- Update configuration files or data files
- Replace entire file contents
- Edit documentation or metadata

Parameters:
- skill_name: The name of the skill directory (e.g., 'my-skill')
- file_path: Relative path to the file to update (e.g., 'scripts/process.py')
- content: The new complete content to write to the file (replaces entire file)

Important:
- This replaces the ENTIRE file content with what you provide
- The file must already exist (use create_skill_file for new files)
- File_path must be relative to the skill's root directory
- Always provide the complete new content, not just changes

Returns: Success message with filename and character count.""",
                inputSchema=UpdateSkillFileInput.model_json_schema(),
            ),
            types.Tool(
                name="delete_skill_file",
                description="""Delete a file from a skill directory permanently.

This tool allows you to:
- Remove files that are no longer needed
- Clean up outdated scripts or data files
- Delete temporary files or corrupted files

Parameters:
- skill_name: The name of the skill directory (e.g., 'my-skill')
- file_path: Relative path to the file to delete (e.g., 'scripts/old_script.py', 'data/temp.csv')

Important:
- This operation is permanent and cannot be undone
- The file must exist or an error will be returned
- File_path must be relative to the skill's root directory
- Cannot delete directories (only individual files)
- Cannot delete outside the skill directory (path traversal prevented)

Returns: Success message confirming deletion.""",
                inputSchema=DeleteSkillFileInput.model_json_schema(),
            ),
        ]
    
    @staticmethod
    async def read_skill_file(input_data: ReadSkillFileInput) -> list[types.TextContent]:
        """Read a skill file."""
        try:
            content = FileService.read_file(input_data.skill_name, input_data.file_path)
            result = f"Content of {input_data.skill_name}/{input_data.file_path}:\n\n{content}"
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]
    
    @staticmethod
    async def create_skill_file(input_data: CreateSkillFileInput) -> list[types.TextContent]:
        """Create a new skill file."""
        try:
            FileService.create_file(input_data.skill_name, input_data.file_path, input_data.content)
            result = f"Successfully created {input_data.skill_name}/{input_data.file_path} ({len(input_data.content)} characters)"
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creating file: {str(e)}")]
    
    @staticmethod
    async def update_skill_file(input_data: UpdateSkillFileInput) -> list[types.TextContent]:
        """Update an existing skill file."""
        try:
            FileService.update_file(input_data.skill_name, input_data.file_path, input_data.content)
            result = f"Successfully updated {input_data.skill_name}/{input_data.file_path} ({len(input_data.content)} characters)"
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error updating file: {str(e)}")]
    
    @staticmethod
    async def delete_skill_file(input_data: DeleteSkillFileInput) -> list[types.TextContent]:
        """Delete a skill file."""
        try:
            FileService.delete_file(input_data.skill_name, input_data.file_path)
            result = f"Successfully deleted {input_data.skill_name}/{input_data.file_path}"
            return [types.TextContent(type="text", text=result)]
        except SkillMCPException as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error deleting file: {str(e)}")]
