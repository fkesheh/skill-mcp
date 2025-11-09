"""Tests for unified skill CRUD tool."""

import pytest

from skill_mcp.core.config import SKILLS_DIR
from skill_mcp.models_crud import SkillCrudInput
from skill_mcp.tools.skill_crud import SkillCrud


@pytest.fixture
def test_skill_name():
    """Provide a test skill name."""
    return "test-crud-skill"


@pytest.fixture
def cleanup_test_skill(test_skill_name):
    """Cleanup test skill after test."""
    yield
    skill_dir = SKILLS_DIR / test_skill_name
    if skill_dir.exists():
        import shutil

        shutil.rmtree(skill_dir)


class TestSkillCrudList:
    """Tests for list operation."""

    @pytest.mark.asyncio
    async def test_list_all_skills(self):
        """Test listing all skills."""
        input_data = SkillCrudInput(operation="list")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "skill(s)" in result[0].text or "No skills found" in result[0].text

    @pytest.mark.asyncio
    async def test_list_with_search(self):
        """Test listing skills with search filter."""
        input_data = SkillCrudInput(operation="list", search="weather")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        # Should either find weather skills or report no matches
        assert "matching 'weather'" in result[0].text


class TestSkillCrudCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_basic_skill(self, test_skill_name, cleanup_test_skill):
        """Test creating a basic skill."""
        input_data = SkillCrudInput(
            operation="create",
            skill_name=test_skill_name,
            description="Test skill",
            template="basic",
        )
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert f"Successfully created skill '{test_skill_name}'" in result[0].text
        assert (SKILLS_DIR / test_skill_name / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_create_python_skill(self, cleanup_test_skill):
        """Test creating a Python skill with template."""
        skill_name = "test-python-skill"
        input_data = SkillCrudInput(
            operation="create",
            skill_name=skill_name,
            description="Python test skill",
            template="python",
        )
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert f"Successfully created skill '{skill_name}'" in result[0].text

        # Cleanup
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists():
            import shutil

            shutil.rmtree(skill_dir)

    @pytest.mark.asyncio
    async def test_create_without_skill_name(self):
        """Test create fails without skill_name."""
        input_data = SkillCrudInput(operation="create")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "skill_name is required" in result[0].text


class TestSkillCrudGet:
    """Tests for get operation."""

    @pytest.mark.asyncio
    async def test_get_existing_skill(self, test_skill_name, cleanup_test_skill):
        """Test getting details of an existing skill."""
        # First create a skill
        create_input = SkillCrudInput(
            operation="create", skill_name=test_skill_name, description="Test skill"
        )
        await SkillCrud.skill_crud(create_input)

        # Now get its details
        get_input = SkillCrudInput(
            operation="get", skill_name=test_skill_name, include_content=True
        )
        result = await SkillCrud.skill_crud(get_input)

        assert len(result) == 1
        assert f"Skill: {test_skill_name}" in result[0].text
        assert "Files (" in result[0].text
        assert "SKILL.md Content" in result[0].text

    @pytest.mark.asyncio
    async def test_get_without_skill_name(self):
        """Test get fails without skill_name."""
        input_data = SkillCrudInput(operation="get")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "skill_name is required" in result[0].text

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill(self):
        """Test getting a nonexistent skill."""
        input_data = SkillCrudInput(operation="get", skill_name="nonexistent-skill-xyz")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_get_shows_file_metadata(self, test_skill_name, cleanup_test_skill):
        """Test that get operation shows file metadata (size and modification time)."""
        import time

        # Create a skill
        create_input = SkillCrudInput(
            operation="create",
            skill_name=test_skill_name,
            description="Test skill",
            template="python",
        )
        await SkillCrud.skill_crud(create_input)

        # Wait a moment to ensure timestamps are set
        time.sleep(0.1)

        # Get skill details
        get_input = SkillCrudInput(operation="get", skill_name=test_skill_name)
        result = await SkillCrud.skill_crud(get_input)

        assert len(result) == 1
        output = result[0].text

        # Should show file list
        assert "Files (" in output

        # Should show SKILL.md with metadata
        assert "SKILL.md" in output

        # Should show file size in bytes
        assert "bytes" in output

        # Should show modification time in readable format (e.g., "modified: 2025-11-09")
        assert "modified:" in output

        # Check that modification date is shown (format: YYYY-MM-DD)
        import re

        assert re.search(r"modified: \d{4}-\d{2}-\d{2}", output), (
            "Should show modification date in YYYY-MM-DD format"
        )

        # If python template was used, should also show main.py with metadata
        if "main.py" in output:
            # Count occurrences of "modified:" - should be at least 2 (SKILL.md + main.py)
            assert output.count("modified:") >= 2


class TestSkillCrudValidate:
    """Tests for validate operation."""

    @pytest.mark.asyncio
    async def test_validate_valid_skill(self, test_skill_name, cleanup_test_skill):
        """Test validating a valid skill."""
        # Create a skill first
        create_input = SkillCrudInput(
            operation="create", skill_name=test_skill_name, description="Test skill"
        )
        await SkillCrud.skill_crud(create_input)

        # Validate it
        validate_input = SkillCrudInput(operation="validate", skill_name=test_skill_name)
        result = await SkillCrud.skill_crud(validate_input)

        assert len(result) == 1
        assert f"Validation for skill '{test_skill_name}'" in result[0].text
        assert "✓ Valid" in result[0].text or "✗ Invalid" in result[0].text

    @pytest.mark.asyncio
    async def test_validate_without_skill_name(self):
        """Test validate fails without skill_name."""
        input_data = SkillCrudInput(operation="validate")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "skill_name is required" in result[0].text


class TestSkillCrudDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_with_confirmation(self, test_skill_name):
        """Test deleting a skill with confirmation."""
        # Create a skill first
        create_input = SkillCrudInput(
            operation="create", skill_name=test_skill_name, description="Test skill"
        )
        await SkillCrud.skill_crud(create_input)

        # Delete it
        delete_input = SkillCrudInput(operation="delete", skill_name=test_skill_name, confirm=True)
        result = await SkillCrud.skill_crud(delete_input)

        assert len(result) == 1
        assert f"Successfully deleted skill '{test_skill_name}'" in result[0].text
        assert not (SKILLS_DIR / test_skill_name).exists()

    @pytest.mark.asyncio
    async def test_delete_without_confirmation(self, test_skill_name, cleanup_test_skill):
        """Test delete fails without confirmation."""
        # Create a skill first
        create_input = SkillCrudInput(
            operation="create", skill_name=test_skill_name, description="Test skill"
        )
        await SkillCrud.skill_crud(create_input)

        # Try to delete without confirm
        delete_input = SkillCrudInput(operation="delete", skill_name=test_skill_name, confirm=False)
        result = await SkillCrud.skill_crud(delete_input)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "confirm=true is required" in result[0].text
        assert (SKILLS_DIR / test_skill_name).exists()

    @pytest.mark.asyncio
    async def test_delete_without_skill_name(self):
        """Test delete fails without skill_name."""
        input_data = SkillCrudInput(operation="delete", confirm=True)
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "skill_name is required" in result[0].text


class TestSkillCrudSearch:
    """Tests for search operation."""

    @pytest.mark.asyncio
    async def test_search_finds_matching_skills(self):
        """Test that search operation finds skills by pattern."""
        # Create test skills
        await SkillCrud.skill_crud(
            SkillCrudInput(
                operation="create", skill_name="weather-skill", description="Weather data fetcher"
            )
        )
        await SkillCrud.skill_crud(
            SkillCrudInput(
                operation="create", skill_name="calculator-skill", description="Simple calculator"
            )
        )

        # Search for "weather"
        search_input = SkillCrudInput(operation="search", search="weather")
        result = await SkillCrud.skill_crud(search_input)

        assert len(result) == 1
        output = result[0].text
        assert "weather-skill" in output
        assert "calculator-skill" not in output

        # Cleanup
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="delete", skill_name="weather-skill", confirm=True)
        )
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="delete", skill_name="calculator-skill", confirm=True)
        )

    @pytest.mark.asyncio
    async def test_search_with_regex_pattern(self):
        """Test search with regex pattern."""
        # Create test skills
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="create", skill_name="test-skill-1", description="First test")
        )
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="create", skill_name="test-skill-2", description="Second test")
        )

        # Search with regex pattern (starts with "test-skill")
        search_input = SkillCrudInput(operation="search", search="^test-skill")
        result = await SkillCrud.skill_crud(search_input)

        assert len(result) == 1
        output = result[0].text
        assert "test-skill-1" in output or "test-skill-2" in output

        # Cleanup
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="delete", skill_name="test-skill-1", confirm=True)
        )
        await SkillCrud.skill_crud(
            SkillCrudInput(operation="delete", skill_name="test-skill-2", confirm=True)
        )

    @pytest.mark.asyncio
    async def test_search_without_pattern(self):
        """Test search fails without pattern."""
        search_input = SkillCrudInput(operation="search")
        result = await SkillCrud.skill_crud(search_input)

        assert len(result) == 1
        assert "Error" in result[0].text or "required" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_search_no_matches(self):
        """Test search returns appropriate message when no matches found."""
        search_input = SkillCrudInput(operation="search", search="nonexistent-xyz-pattern-12345")
        result = await SkillCrud.skill_crud(search_input)

        assert len(result) == 1
        output = result[0].text
        assert "No skills found" in output or "0 skill" in output


class TestSkillCrudInvalidOperation:
    """Tests for invalid operations."""

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Test unknown operation."""
        input_data = SkillCrudInput(operation="invalid_op")
        result = await SkillCrud.skill_crud(input_data)

        assert len(result) == 1
        assert "Unknown operation" in result[0].text
        assert "invalid_op" in result[0].text
