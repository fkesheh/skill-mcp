"""Template management service."""

from dataclasses import dataclass
from typing import Dict, List

from skill_mcp.core.exceptions import InvalidTemplateError


@dataclass
class TemplateSpec:
    """Specification for a skill template."""

    name: str
    description: str
    files: List[str]

    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "files": self.files,
        }


class TemplateRegistry:
    """Registry of available skill templates."""

    # Template definitions
    TEMPLATES = {
        "basic": TemplateSpec(
            name="basic",
            description="Minimal skill with only SKILL.md",
            files=["SKILL.md"],
        ),
        "python": TemplateSpec(
            name="python",
            description="Python skill with main script",
            files=["SKILL.md", "main.py"],
        ),
        "bash": TemplateSpec(
            name="bash", description="Bash script skill", files=["SKILL.md", "main.sh"]
        ),
    }

    @staticmethod
    def list_templates() -> Dict[str, TemplateSpec]:
        """
        List all available templates.

        Returns:
            Dictionary mapping template names to TemplateSpec objects
        """
        return TemplateRegistry.TEMPLATES.copy()

    @staticmethod
    def get_template(template_name: str) -> TemplateSpec:
        """
        Get a specific template spec.

        Args:
            template_name: Name of the template

        Returns:
            TemplateSpec object

        Raises:
            InvalidTemplateError: If template doesn't exist
        """
        if template_name not in TemplateRegistry.TEMPLATES:
            available = ", ".join(TemplateRegistry.TEMPLATES.keys())
            raise InvalidTemplateError(
                f"Invalid template '{template_name}'. Available templates: {available}"
            )
        return TemplateRegistry.TEMPLATES[template_name]

    @staticmethod
    def validate_template(template_name: str) -> None:
        """
        Validate that a template name is valid.

        Args:
            template_name: Name of the template to validate

        Raises:
            InvalidTemplateError: If template is invalid
        """
        # This just calls get_template which raises if invalid
        TemplateRegistry.get_template(template_name)
