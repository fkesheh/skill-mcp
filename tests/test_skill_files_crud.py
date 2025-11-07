"""Tests for unified skill files CRUD tool."""

import pytest

from skill_mcp.core.config import SKILLS_DIR
from skill_mcp.models_crud import FileSpec, SkillFilesCrudInput
from skill_mcp.tools.skill_files_crud import SkillFilesCrud


@pytest.fixture
def test_skill_name():
    """Provide a test skill name."""
    return "test-files-skill"


@pytest.fixture
def setup_test_skill(test_skill_name):
    """Create a test skill directory."""
    skill_dir = SKILLS_DIR / test_skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("---\nname: Test Skill\ndescription: Test\n---\n# Test")

    yield test_skill_name

    # Cleanup
    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)


class TestSkillFilesCrudCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_single_file(self, setup_test_skill):
        """Test creating a single file."""
        input_data = SkillFilesCrudInput(
            operation="create",
            skill_name=setup_test_skill,
            file_path="test.py",
            content="print('hello')",
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully created file 'test.py'" in result[0].text
        assert (SKILLS_DIR / setup_test_skill / "test.py").exists()

    @pytest.mark.asyncio
    async def test_create_multiple_files(self, setup_test_skill):
        """Test creating multiple files in bulk."""
        files = [
            FileSpec(path="file1.py", content="# File 1"),
            FileSpec(path="file2.py", content="# File 2"),
            FileSpec(path="file3.py", content="# File 3"),
        ]

        input_data = SkillFilesCrudInput(
            operation="create", skill_name=setup_test_skill, files=files, atomic=True
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully created 3 files" in result[0].text
        assert (SKILLS_DIR / setup_test_skill / "file1.py").exists()
        assert (SKILLS_DIR / setup_test_skill / "file2.py").exists()
        assert (SKILLS_DIR / setup_test_skill / "file3.py").exists()

    @pytest.mark.asyncio
    async def test_create_with_nested_path(self, setup_test_skill):
        """Test creating a file in a nested directory."""
        input_data = SkillFilesCrudInput(
            operation="create",
            skill_name=setup_test_skill,
            file_path="src/utils.py",
            content="# Utils",
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully created file 'src/utils.py'" in result[0].text
        assert (SKILLS_DIR / setup_test_skill / "src" / "utils.py").exists()

    @pytest.mark.asyncio
    async def test_create_cannot_mix_single_and_bulk(self, setup_test_skill):
        """Test that cannot specify both single and bulk parameters."""
        files = [FileSpec(path="file1.py", content="# File 1")]

        input_data = SkillFilesCrudInput(
            operation="create",
            skill_name=setup_test_skill,
            file_path="test.py",  # Single
            content="test",  # Single
            files=files,  # Bulk
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "Cannot specify both" in result[0].text

    @pytest.mark.asyncio
    async def test_create_without_content(self, setup_test_skill):
        """Test create fails without content."""
        input_data = SkillFilesCrudInput(
            operation="create", skill_name=setup_test_skill, file_path="test.py"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text


class TestSkillFilesCrudRead:
    """Tests for read operation."""

    @pytest.mark.asyncio
    async def test_read_existing_file(self, setup_test_skill):
        """Test reading an existing file."""
        # Create a file first
        test_content = "# Test content"
        test_file = SKILLS_DIR / setup_test_skill / "test.py"
        test_file.write_text(test_content)

        # Read it
        input_data = SkillFilesCrudInput(
            operation="read", skill_name=setup_test_skill, file_path="test.py"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "=== test.py ===" in result[0].text
        assert test_content in result[0].text

    @pytest.mark.asyncio
    async def test_read_without_file_path(self, setup_test_skill):
        """Test read fails without file_path."""
        input_data = SkillFilesCrudInput(operation="read", skill_name=setup_test_skill)
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "file_path is required" in result[0].text

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, setup_test_skill):
        """Test reading a nonexistent file."""
        input_data = SkillFilesCrudInput(
            operation="read", skill_name=setup_test_skill, file_path="nonexistent.py"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text


class TestSkillFilesCrudUpdate:
    """Tests for update operation."""

    @pytest.mark.asyncio
    async def test_update_single_file(self, setup_test_skill):
        """Test updating a single file."""
        # Create a file first
        test_file = SKILLS_DIR / setup_test_skill / "test.py"
        test_file.write_text("# Original")

        # Update it
        new_content = "# Updated content"
        input_data = SkillFilesCrudInput(
            operation="update",
            skill_name=setup_test_skill,
            file_path="test.py",
            content=new_content,
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully updated file 'test.py'" in result[0].text
        assert test_file.read_text() == new_content

    @pytest.mark.asyncio
    async def test_update_multiple_files(self, setup_test_skill):
        """Test updating multiple files in bulk."""
        # Create files first
        (SKILLS_DIR / setup_test_skill / "file1.py").write_text("# Original 1")
        (SKILLS_DIR / setup_test_skill / "file2.py").write_text("# Original 2")

        # Update them
        files = [
            FileSpec(path="file1.py", content="# Updated 1"),
            FileSpec(path="file2.py", content="# Updated 2"),
        ]

        input_data = SkillFilesCrudInput(
            operation="update", skill_name=setup_test_skill, files=files
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully updated 2 files" in result[0].text
        assert (SKILLS_DIR / setup_test_skill / "file1.py").read_text() == "# Updated 1"
        assert (SKILLS_DIR / setup_test_skill / "file2.py").read_text() == "# Updated 2"

    @pytest.mark.asyncio
    async def test_update_without_content(self, setup_test_skill):
        """Test update fails without content."""
        input_data = SkillFilesCrudInput(
            operation="update", skill_name=setup_test_skill, file_path="test.py"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text


class TestSkillFilesCrudDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, setup_test_skill):
        """Test deleting an existing file."""
        # Create a file first
        test_file = SKILLS_DIR / setup_test_skill / "test.py"
        test_file.write_text("# Test")

        # Delete it
        input_data = SkillFilesCrudInput(
            operation="delete", skill_name=setup_test_skill, file_path="test.py"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Successfully deleted file 'test.py'" in result[0].text
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_without_file_path(self, setup_test_skill):
        """Test delete fails without file_path."""
        input_data = SkillFilesCrudInput(operation="delete", skill_name=setup_test_skill)
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "file_path is required" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_protected_skill_md(self, setup_test_skill):
        """Test that SKILL.md cannot be deleted through CRUD."""
        # Verify SKILL.md exists
        skill_md = SKILLS_DIR / setup_test_skill / "SKILL.md"
        assert skill_md.exists()

        # Try to delete it
        input_data = SkillFilesCrudInput(
            operation="delete", skill_name=setup_test_skill, file_path="SKILL.md"
        )
        result = await SkillFilesCrud.skill_files_crud(input_data)

        # Should fail with error
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "protected" in result[0].text.lower() or "cannot delete" in result[0].text.lower()
        # Verify SKILL.md still exists
        assert skill_md.exists()


class TestSkillFilesCrudInvalidOperation:
    """Tests for invalid operations."""

    @pytest.mark.asyncio
    async def test_unknown_operation(self, setup_test_skill):
        """Test unknown operation."""
        input_data = SkillFilesCrudInput(operation="invalid_op", skill_name=setup_test_skill)
        result = await SkillFilesCrud.skill_files_crud(input_data)

        assert len(result) == 1
        assert "Unknown operation" in result[0].text
        assert "invalid_op" in result[0].text
