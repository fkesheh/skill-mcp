"""YAML frontmatter parsing utilities."""

import yaml
from typing import Optional, Dict, Any


def parse_yaml_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse YAML frontmatter from markdown content.
    
    Frontmatter is expected to be between --- markers at the start of the file:
    ---
    name: skill-name
    description: A description of the skill
    ---
    
    Args:
        content: File content with optional YAML frontmatter
        
    Returns:
        Dictionary with parsed YAML, or None if no frontmatter found
    """
    if not content.startswith("---"):
        return None
    
    try:
        # Find the closing --- marker
        lines = content.split("\n")
        if len(lines) < 2:
            return None
        
        # Find end of frontmatter
        end_index = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_index = i
                break
        
        if end_index is None:
            return None
        
        # Extract and parse YAML
        frontmatter_content = "\n".join(lines[1:end_index])
        data = yaml.safe_load(frontmatter_content)
        
        return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        return None


def get_skill_description(metadata: Optional[Dict[str, Any]]) -> str:
    """
    Extract description from skill metadata.
    
    Args:
        metadata: Parsed YAML frontmatter
        
    Returns:
        Description string, or empty string if not found
    """
    if not metadata:
        return ""
    return metadata.get("description", "")


def get_skill_name(metadata: Optional[Dict[str, Any]]) -> str:
    """
    Extract skill name from metadata.
    
    Args:
        metadata: Parsed YAML frontmatter
        
    Returns:
        Name string, or empty string if not found
    """
    if not metadata:
        return ""
    return metadata.get("name", "")
