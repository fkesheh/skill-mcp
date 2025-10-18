"""Tests for YAML frontmatter parsing."""

import pytest
from skill_mcp.utils.yaml_parser import parse_yaml_frontmatter, get_skill_description, get_skill_name


def test_parse_valid_frontmatter():
    """Test parsing valid YAML frontmatter."""
    content = """---
name: test-skill
description: A test skill
author: Test Author
---

# Content here
"""
    result = parse_yaml_frontmatter(content)
    
    assert result is not None
    assert result["name"] == "test-skill"
    assert result["description"] == "A test skill"
    assert result["author"] == "Test Author"


def test_parse_no_frontmatter():
    """Test parsing content without frontmatter."""
    content = "# Content without frontmatter\nSome text here"
    result = parse_yaml_frontmatter(content)
    
    assert result is None


def test_parse_incomplete_frontmatter():
    """Test parsing incomplete frontmatter."""
    content = """---
name: test-skill
no closing marker"""
    result = parse_yaml_frontmatter(content)
    
    assert result is None


def test_get_skill_description():
    """Test extracting skill description."""
    metadata = {
        "name": "test",
        "description": "Test description"
    }
    
    desc = get_skill_description(metadata)
    assert desc == "Test description"


def test_get_skill_description_empty():
    """Test getting description from empty metadata."""
    desc = get_skill_description(None)
    assert desc == ""
    
    desc = get_skill_description({})
    assert desc == ""


def test_get_skill_name():
    """Test extracting skill name."""
    metadata = {"name": "my-skill"}
    
    name = get_skill_name(metadata)
    assert name == "my-skill"


def test_get_skill_name_empty():
    """Test getting name from empty metadata."""
    name = get_skill_name(None)
    assert name == ""
    
    name = get_skill_name({})
    assert name == ""
