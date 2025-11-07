"""Tests for unified skill environment CRUD tool."""

import pytest

from skill_mcp.core.config import ENV_FILE_NAME, SKILLS_DIR
from skill_mcp.models_crud import SkillEnvCrudInput
from skill_mcp.tools.skill_env_crud import SkillEnvCrud


@pytest.fixture
def test_skill_name():
    """Provide a test skill name."""
    return "test-env-skill"


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


class TestSkillEnvCrudRead:
    """Tests for read operation."""

    @pytest.mark.asyncio
    async def test_read_empty_env(self, setup_test_skill):
        """Test reading environment with no variables."""
        input_data = SkillEnvCrudInput(operation="read", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "No environment variables" in result[0].text

    @pytest.mark.asyncio
    async def test_read_existing_env_vars(self, setup_test_skill):
        """Test reading existing environment variables."""
        # Create env file
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        env_file.write_text("API_KEY=test123\nDEBUG=true\n")

        input_data = SkillEnvCrudInput(operation="read", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "API_KEY" in result[0].text
        assert "DEBUG" in result[0].text
        assert "test123" not in result[0].text  # Values should be hidden


class TestSkillEnvCrudSet:
    """Tests for set operation."""

    @pytest.mark.asyncio
    async def test_set_single_variable_smart_mode(self, setup_test_skill):
        """Test setting a single variable in smart mode."""
        input_data = SkillEnvCrudInput(
            operation="set",
            skill_name=setup_test_skill,
            variables={"API_KEY": "sk-123"},
            mode="smart",
        )
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Successfully set 1 environment variable(s)" in result[0].text

        # Verify it was written
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        assert env_file.exists()
        content = env_file.read_text()
        assert "API_KEY=sk-123" in content

    @pytest.mark.asyncio
    async def test_set_multiple_variables_merge_mode(self, setup_test_skill):
        """Test setting multiple variables in merge mode."""
        # Set initial vars
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        env_file.write_text("EXISTING=value\n")

        # Add more vars
        input_data = SkillEnvCrudInput(
            operation="set",
            skill_name=setup_test_skill,
            variables={"API_KEY": "sk-123", "DEBUG": "true", "TIMEOUT": "30"},
            mode="merge",
        )
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Successfully set 3 environment variable(s)" in result[0].text

        # Verify merge preserved existing var
        content = env_file.read_text()
        assert "EXISTING=value" in content
        assert "API_KEY=sk-123" in content
        assert "DEBUG=true" in content
        assert "TIMEOUT=30" in content

    @pytest.mark.asyncio
    async def test_set_without_variables(self, setup_test_skill):
        """Test set fails without variables."""
        input_data = SkillEnvCrudInput(operation="set", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "variables is required" in result[0].text


class TestSkillEnvCrudDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_single_variable(self, setup_test_skill):
        """Test deleting a single variable."""
        # Create env file with multiple vars
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        env_file.write_text("API_KEY=sk-123\nDEBUG=true\nTIMEOUT=30\n")

        # Delete one var
        input_data = SkillEnvCrudInput(
            operation="delete", skill_name=setup_test_skill, keys=["DEBUG"]
        )
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Successfully deleted 1 environment variable(s)" in result[0].text

        # Verify only DEBUG was deleted
        content = env_file.read_text()
        assert "API_KEY=sk-123" in content
        assert "DEBUG" not in content
        assert "TIMEOUT=30" in content

    @pytest.mark.asyncio
    async def test_delete_multiple_variables(self, setup_test_skill):
        """Test deleting multiple variables in bulk."""
        # Create env file
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        env_file.write_text("API_KEY=sk-123\nDEBUG=true\nTIMEOUT=30\nKEEP=this\n")

        # Delete multiple vars
        input_data = SkillEnvCrudInput(
            operation="delete", skill_name=setup_test_skill, keys=["API_KEY", "DEBUG", "TIMEOUT"]
        )
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Successfully deleted 3 environment variable(s)" in result[0].text

        # Verify only KEEP remains
        content = env_file.read_text()
        assert "KEEP=this" in content
        assert "API_KEY" not in content
        assert "DEBUG" not in content
        assert "TIMEOUT" not in content

    @pytest.mark.asyncio
    async def test_delete_without_keys(self, setup_test_skill):
        """Test delete fails without keys."""
        input_data = SkillEnvCrudInput(operation="delete", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "keys is required" in result[0].text


class TestSkillEnvCrudClear:
    """Tests for clear operation."""

    @pytest.mark.asyncio
    async def test_clear_all_variables(self, setup_test_skill):
        """Test clearing all environment variables."""
        # Create env file with vars
        env_file = SKILLS_DIR / setup_test_skill / ENV_FILE_NAME
        env_file.write_text("API_KEY=sk-123\nDEBUG=true\nTIMEOUT=30\n")

        # Clear all
        input_data = SkillEnvCrudInput(operation="clear", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Successfully cleared all environment variables" in result[0].text

        # Verify file is empty or doesn't exist
        assert not env_file.exists() or env_file.read_text() == ""

    @pytest.mark.asyncio
    async def test_clear_when_no_env_file(self, setup_test_skill):
        """Test clearing when no env file exists."""
        input_data = SkillEnvCrudInput(operation="clear", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        # Should succeed or report no file
        assert "cleared" in result[0].text.lower() or "exists" in result[0].text.lower()


class TestSkillEnvCrudInvalidOperation:
    """Tests for invalid operations."""

    @pytest.mark.asyncio
    async def test_unknown_operation(self, setup_test_skill):
        """Test unknown operation."""
        input_data = SkillEnvCrudInput(operation="invalid_op", skill_name=setup_test_skill)
        result = await SkillEnvCrud.skill_env_crud(input_data)

        assert len(result) == 1
        assert "Unknown operation" in result[0].text
        assert "invalid_op" in result[0].text
