"""Tests for template validation - reproduces Bug #4."""

import pytest

from skill_mcp.core.config import SKILLS_DIR
from skill_mcp.models_crud import SkillCrudInput
from skill_mcp.tools.skill_crud import SkillCrud


class TestTemplateBugReproduction:
    """Reproduce the confirmed template bug from agent testing."""

    @pytest.mark.asyncio
    async def test_bug_invalid_template_should_raise_error(
        self, test_skill_name, cleanup_test_skill
    ):
        """
        BUG REPRODUCTION: Invalid template silently falls back to basic.

        Expected: Error message listing valid templates
        Actual: Silently creates basic skill with no error
        """
        input_data = SkillCrudInput(
            operation="create",
            skill_name=test_skill_name,
            template="completely-invalid-template-name",
        )
        result = await SkillCrud.skill_crud(input_data)

        # Should raise error
        assert "Error" in result[0].text or "error" in result[0].text, (
            "Bug reproduced: Invalid template doesn't raise error"
        )
        assert "invalid" in result[0].text.lower()
        assert "available" in result[0].text.lower() or "valid" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_bug_api_client_template_not_implemented(
        self, test_skill_name, cleanup_test_skill
    ):
        """
        BUG REPRODUCTION: api-client template documented but not implemented.

        Expected: Creates api-client specific files OR raises error
        Actual: Falls back to basic (only SKILL.md)
        """
        input_data = SkillCrudInput(
            operation="create", skill_name=test_skill_name, template="api-client"
        )
        result = await SkillCrud.skill_crud(input_data)

        # Should raise error since api-client is not implemented
        assert "Error" in result[0].text or "Invalid" in result[0].text, (
            "Bug reproduced: api-client should raise error (not implemented)"
        )
        assert "api-client" in result[0].text

    @pytest.mark.asyncio
    async def test_bug_list_templates_doesnt_exist(self):
        """
        BUG REPRODUCTION: No list_templates operation.

        Expected: Returns list of available templates
        Actual: "Unknown operation"
        """
        input_data = SkillCrudInput(operation="list_templates")
        result = await SkillCrud.skill_crud(input_data)

        # Should NOT say "Unknown operation"
        assert "Unknown operation" not in result[0].text, (
            "Bug reproduced: list_templates operation doesn't exist"
        )

        # Should list templates
        assert "basic" in result[0].text
        assert "python" in result[0].text
        assert "bash" in result[0].text


class TestTemplateValidation:
    """Tests for template validation (after fix)."""

    @pytest.mark.asyncio
    async def test_valid_templates_work(self, test_skill_name, cleanup_test_skill):
        """Test that valid templates create correct files."""
        # Test python template
        input_data = SkillCrudInput(
            operation="create", skill_name=test_skill_name, template="python"
        )
        result = await SkillCrud.skill_crud(input_data)

        assert "Error" not in result[0].text
        skill_dir = SKILLS_DIR / test_skill_name
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "main.py").exists()

    @pytest.mark.asyncio
    async def test_bash_template_works(self, test_skill_name, cleanup_test_skill):
        """Test that bash template creates correct files."""
        input_data = SkillCrudInput(operation="create", skill_name=test_skill_name, template="bash")
        result = await SkillCrud.skill_crud(input_data)

        assert "Error" not in result[0].text
        skill_dir = SKILLS_DIR / test_skill_name
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "main.sh").exists()

    @pytest.mark.asyncio
    async def test_basic_template_works(self, test_skill_name, cleanup_test_skill):
        """Test that basic template creates only SKILL.md."""
        input_data = SkillCrudInput(
            operation="create", skill_name=test_skill_name, template="basic"
        )
        result = await SkillCrud.skill_crud(input_data)

        assert "Error" not in result[0].text
        skill_dir = SKILLS_DIR / test_skill_name
        assert (skill_dir / "SKILL.md").exists()

        # Should not create other files
        files = [f.name for f in skill_dir.glob("*")]
        assert files == ["SKILL.md"]

    @pytest.mark.asyncio
    async def test_typo_in_template_gives_helpful_error(self, test_skill_name, cleanup_test_skill):
        """Test that typos like 'pythoon' give clear error."""
        input_data = SkillCrudInput(
            operation="create",
            skill_name=test_skill_name,
            template="pythoon",  # Typo
        )
        result = await SkillCrud.skill_crud(input_data)

        # Should show error
        assert "Error" in result[0].text or "Invalid" in result[0].text
        # Should mention the typo
        assert "pythoon" in result[0].text
        # Should suggest valid templates
        assert "python" in result[0].text or "bash" in result[0].text or "basic" in result[0].text


class TestTemplateDiscovery:
    """Tests for template discovery."""

    @pytest.mark.asyncio
    async def test_list_templates_shows_all(self):
        """Test list_templates operation shows all available templates."""
        input_data = SkillCrudInput(operation="list_templates")
        result = await SkillCrud.skill_crud(input_data)

        text = result[0].text

        # Should list all templates
        assert "basic" in text
        assert "python" in text
        assert "bash" in text

        # Should NOT list api-client (not implemented)
        # If it appears, it should be marked as removed/deprecated

    @pytest.mark.asyncio
    async def test_list_templates_describes_files(self):
        """Test that list_templates shows which files each template creates."""
        input_data = SkillCrudInput(operation="list_templates")
        result = await SkillCrud.skill_crud(input_data)

        text = result[0].text

        # Should mention files for each template
        assert "SKILL.md" in text
        assert "main.py" in text  # Python template
        assert "main.sh" in text  # Bash template

    @pytest.mark.asyncio
    async def test_list_templates_has_descriptions(self):
        """Test that list_templates includes template descriptions."""
        input_data = SkillCrudInput(operation="list_templates")
        result = await SkillCrud.skill_crud(input_data)

        text = result[0].text.lower()

        # Should include descriptions
        assert "description" in text or ":" in result[0].text
