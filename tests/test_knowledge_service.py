"""Tests for knowledge document service."""

import pytest
from pathlib import Path
from skill_mcp.services.knowledge_service import KnowledgeService


@pytest.fixture
def tmp_knowledge_dir(tmp_path, monkeypatch):
    """Create temporary knowledge directory for testing."""
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    monkeypatch.setattr("skill_mcp.services.knowledge_service.KNOWLEDGE_DIR", knowledge_dir)
    return knowledge_dir


class TestKnowledgeServiceHelpers:
    """Test helper methods."""

    def test_sanitize_knowledge_id_valid(self):
        """Test sanitizing a valid knowledge ID."""
        result = KnowledgeService._sanitize_knowledge_id("my-knowledge-123")
        assert result == "my-knowledge-123"

    def test_sanitize_knowledge_id_with_spaces(self):
        """Test sanitizing ID with spaces."""
        result = KnowledgeService._sanitize_knowledge_id("my knowledge doc")
        assert result == "my_knowledge_doc"

    def test_sanitize_knowledge_id_with_special_chars(self):
        """Test sanitizing ID with special characters."""
        result = KnowledgeService._sanitize_knowledge_id("my@knowledge#doc!")
        assert result == "my_knowledge_doc_"

    def test_sanitize_knowledge_id_with_slashes(self):
        """Test sanitizing ID with path separators."""
        result = KnowledgeService._sanitize_knowledge_id("docs/tutorial/intro")
        assert result == "docs_tutorial_intro"

    def test_parse_frontmatter_with_valid_frontmatter(self):
        """Test parsing markdown with valid frontmatter."""
        content = """---
id: test-doc
title: Test Document
category: tutorial
tags: python, testing
author: Test Author
---

# Content here
This is the actual content.
"""
        metadata, actual_content = KnowledgeService._parse_frontmatter(content)

        assert metadata["id"] == "test-doc"
        assert metadata["title"] == "Test Document"
        assert metadata["category"] == "tutorial"
        assert metadata["tags"] == ["python", "testing"]
        assert metadata["author"] == "Test Author"
        assert "# Content here" in actual_content
        assert "This is the actual content." in actual_content

    def test_parse_frontmatter_without_frontmatter(self):
        """Test parsing markdown without frontmatter."""
        content = "# Just content\nNo frontmatter here."
        metadata, actual_content = KnowledgeService._parse_frontmatter(content)

        assert metadata["id"] == ""
        assert metadata["title"] == ""
        assert metadata["category"] == "note"
        assert metadata["tags"] == []
        assert metadata["author"] == "Unknown"
        assert actual_content == content

    def test_parse_frontmatter_with_empty_tags(self):
        """Test parsing frontmatter with empty tags."""
        content = """---
id: test
title: Test
tags:
---

Content"""
        metadata, actual_content = KnowledgeService._parse_frontmatter(content)
        assert metadata["tags"] == []

    def test_parse_frontmatter_with_tags_containing_empty_items(self):
        """Test parsing tags with empty items."""
        content = """---
tags: python, , testing,
---

Content"""
        metadata, actual_content = KnowledgeService._parse_frontmatter(content)
        assert metadata["tags"] == ["python", "testing"]

    def test_create_frontmatter_basic(self):
        """Test creating basic frontmatter."""
        result = KnowledgeService._create_frontmatter(
            "test-id", "Test Title", "tutorial", ["python", "testing"], "Test Author"
        )

        assert "---" in result
        assert "id: test-id" in result
        assert "title: Test Title" in result
        assert "category: tutorial" in result
        assert "tags: python, testing" in result
        assert "author: Test Author" in result

    def test_create_frontmatter_with_no_tags(self):
        """Test creating frontmatter with no tags."""
        result = KnowledgeService._create_frontmatter(
            "test-id", "Test Title", "note", None, None
        )

        assert "tags:" in result
        assert "author: Unknown" in result

    def test_create_frontmatter_with_empty_tags_list(self):
        """Test creating frontmatter with empty tags list."""
        result = KnowledgeService._create_frontmatter(
            "test-id", "Test Title", "note", [], None
        )

        assert "tags:" in result


class TestKnowledgeServiceCRUD:
    """Test CRUD operations."""

    def test_create_knowledge_basic(self, tmp_knowledge_dir):
        """Test creating a basic knowledge document."""
        result_path = KnowledgeService.create_knowledge(
            "test-doc",
            "Test Document",
            "This is test content.",
            "tutorial",
            ["python", "testing"],
            "Test Author"
        )

        assert result_path.exists()
        assert result_path.name == "test-doc.md"

        content = result_path.read_text()
        assert "id: test-doc" in content
        assert "title: Test Document" in content
        assert "This is test content." in content

    def test_create_knowledge_with_special_id(self, tmp_knowledge_dir):
        """Test creating knowledge with special characters in ID."""
        result_path = KnowledgeService.create_knowledge(
            "test doc @ 2024",
            "Test Document",
            "Content",
            "note",
            None,
            None
        )

        assert result_path.exists()
        assert result_path.name == "test_doc___2024.md"

    def test_create_knowledge_minimal(self, tmp_knowledge_dir):
        """Test creating knowledge with minimal parameters."""
        result_path = KnowledgeService.create_knowledge(
            "minimal",
            "Minimal Doc",
            "Minimal content"
        )

        assert result_path.exists()
        content = result_path.read_text()
        assert "category: note" in content
        assert "author: Unknown" in content

    def test_get_knowledge_existing(self, tmp_knowledge_dir):
        """Test getting an existing knowledge document."""
        # Create a document first
        KnowledgeService.create_knowledge(
            "get-test",
            "Get Test",
            "Test content for get.",
            "guide",
            ["tag1", "tag2"],
            "Author"
        )

        result = KnowledgeService.get_knowledge("get-test")

        assert result["id"] == "get-test"
        assert result["title"] == "Get Test"
        assert result["content"] == "Test content for get."
        assert result["category"] == "guide"
        assert result["tags"] == ["tag1", "tag2"]
        assert result["author"] == "Author"

    def test_get_knowledge_nonexistent(self, tmp_knowledge_dir):
        """Test getting a non-existent knowledge document."""
        with pytest.raises(FileNotFoundError) as exc_info:
            KnowledgeService.get_knowledge("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_update_knowledge_existing(self, tmp_knowledge_dir):
        """Test updating an existing knowledge document."""
        # Create initial document
        KnowledgeService.create_knowledge(
            "update-test",
            "Original Title",
            "Original content",
            "tutorial",
            ["tag1"],
            "Author"
        )

        # Update it
        result_path = KnowledgeService.update_knowledge(
            "update-test",
            "Updated Title",
            "Updated content"
        )

        assert result_path.exists()

        # Verify update
        result = KnowledgeService.get_knowledge("update-test")
        assert result["title"] == "Updated Title"
        assert result["content"] == "Updated content"
        # Should preserve other metadata
        assert result["category"] == "tutorial"
        assert result["tags"] == ["tag1"]
        assert result["author"] == "Author"

    def test_update_knowledge_nonexistent(self, tmp_knowledge_dir):
        """Test updating a non-existent knowledge document."""
        with pytest.raises(FileNotFoundError) as exc_info:
            KnowledgeService.update_knowledge("nonexistent", "Title", "Content")

        assert "not found" in str(exc_info.value)

    def test_delete_knowledge_existing(self, tmp_knowledge_dir):
        """Test deleting an existing knowledge document."""
        # Create a document
        path = KnowledgeService.create_knowledge(
            "delete-test",
            "Delete Test",
            "Content to delete"
        )

        assert path.exists()

        # Delete it
        KnowledgeService.delete_knowledge("delete-test")

        assert not path.exists()

    def test_delete_knowledge_nonexistent(self, tmp_knowledge_dir):
        """Test deleting a non-existent knowledge document (should be idempotent)."""
        # Should not raise an error
        KnowledgeService.delete_knowledge("nonexistent")

    def test_list_all_knowledge_empty(self, tmp_knowledge_dir):
        """Test listing knowledge when directory is empty."""
        result = KnowledgeService.list_all_knowledge()
        assert result == []

    def test_list_all_knowledge_with_documents(self, tmp_knowledge_dir):
        """Test listing knowledge with multiple documents."""
        # Create multiple documents
        KnowledgeService.create_knowledge("doc1", "Doc 1", "Content 1", "tutorial", ["tag1"])
        KnowledgeService.create_knowledge("doc2", "Doc 2", "Content 2", "guide", ["tag2"])
        KnowledgeService.create_knowledge("doc3", "Doc 3", "Content 3", "note", [])

        result = KnowledgeService.list_all_knowledge()

        assert len(result) == 3

        # Check that all documents are present
        ids = [doc["id"] for doc in result]
        assert "doc1" in ids
        assert "doc2" in ids
        assert "doc3" in ids

        # Check metadata is included
        doc1 = next(doc for doc in result if doc["id"] == "doc1")
        assert doc1["title"] == "Doc 1"
        assert doc1["category"] == "tutorial"
        assert doc1["tags"] == ["tag1"]

    def test_list_all_knowledge_with_invalid_file(self, tmp_knowledge_dir):
        """Test listing knowledge with an invalid markdown file."""
        # Create a valid document
        KnowledgeService.create_knowledge("valid", "Valid Doc", "Content")

        # Create an invalid file (not proper markdown)
        invalid_file = tmp_knowledge_dir / "invalid.md"
        invalid_file.write_text("Not proper format")

        # Should skip invalid file and return valid one
        result = KnowledgeService.list_all_knowledge()

        assert len(result) >= 1
        assert any(doc["id"] == "valid" for doc in result)

    def test_create_and_get_knowledge_preserves_content_formatting(self, tmp_knowledge_dir):
        """Test that content formatting is preserved."""
        content = """# Heading

## Subheading

- List item 1
- List item 2

```python
def example():
    pass
```

**Bold text** and *italic text*."""

        KnowledgeService.create_knowledge(
            "formatted",
            "Formatted Doc",
            content
        )

        result = KnowledgeService.get_knowledge("formatted")
        assert result["content"] == content
