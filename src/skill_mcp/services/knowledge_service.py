"""Knowledge document management service."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from skill_mcp.core.config import KNOWLEDGE_DIR


class KnowledgeService:
    """Service for managing knowledge documents."""

    @staticmethod
    def _sanitize_knowledge_id(knowledge_id: str) -> str:
        """
        Sanitize knowledge ID for safe filename usage.

        Args:
            knowledge_id: Raw knowledge ID

        Returns:
            Sanitized ID safe for filesystem
        """
        return re.sub(r'[^\w\-]', '_', knowledge_id)

    @staticmethod
    def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content with frontmatter

        Returns:
            Tuple of (metadata dict, actual content string)
        """
        metadata: Dict[str, Any] = {
            "id": "",
            "title": "",
            "category": "note",
            "tags": [],
            "author": "Unknown",
        }
        actual_content = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                actual_content = parts[2].strip()

                for line in frontmatter.split("\n"):
                    if ":" not in line:
                        continue
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "tags":
                        metadata["tags"] = [t.strip() for t in value.split(",") if t.strip()]
                    else:
                        metadata[key] = value

        return metadata, actual_content

    @staticmethod
    def _create_frontmatter(
        knowledge_id: str,
        title: str,
        category: str,
        tags: Optional[List[str]],
        author: Optional[str],
    ) -> str:
        """
        Create YAML frontmatter for knowledge document.

        Args:
            knowledge_id: Document ID
            title: Document title
            category: Category
            tags: List of tags
            author: Author name

        Returns:
            Formatted frontmatter string
        """
        return f"""---
id: {knowledge_id}
title: {title}
category: {category}
tags: {', '.join(tags or [])}
author: {author or 'Unknown'}
---

"""

    @staticmethod
    def create_knowledge(
        knowledge_id: str,
        title: str,
        content: str,
        category: str = "note",
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
    ) -> Path:
        """
        Create a new knowledge document.

        Args:
            knowledge_id: Unique identifier (used as filename)
            title: Title of the document
            content: Markdown content
            category: Category (tutorial, guide, reference, note, article)
            tags: List of tags
            author: Author name

        Returns:
            Path to the created file
        """
        safe_id = KnowledgeService._sanitize_knowledge_id(knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        frontmatter = KnowledgeService._create_frontmatter(
            knowledge_id, title, category, tags, author
        )
        full_content = frontmatter + content

        file_path.write_text(full_content, encoding="utf-8")
        return file_path

    @staticmethod
    def update_knowledge(knowledge_id: str, title: str, content: str) -> Path:
        """
        Update existing knowledge document.

        Args:
            knowledge_id: ID of the document
            title: New title
            content: New content

        Returns:
            Path to the updated file
        """
        safe_id = KnowledgeService._sanitize_knowledge_id(knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Knowledge document '{knowledge_id}' not found")

        # Parse existing frontmatter
        existing_content = file_path.read_text(encoding="utf-8")
        metadata, _ = KnowledgeService._parse_frontmatter(existing_content)

        # Update title in metadata
        metadata["title"] = title

        # Recreate document with updated frontmatter
        frontmatter = KnowledgeService._create_frontmatter(
            metadata.get("id", knowledge_id),
            title,
            metadata.get("category", "note"),
            metadata.get("tags", []),
            metadata.get("author", "Unknown"),
        )
        full_content = frontmatter + content

        file_path.write_text(full_content, encoding="utf-8")
        return file_path

    @staticmethod
    def delete_knowledge(knowledge_id: str) -> None:
        """Delete a knowledge document."""
        safe_id = KnowledgeService._sanitize_knowledge_id(knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if file_path.exists():
            file_path.unlink()

    @staticmethod
    def get_knowledge(knowledge_id: str) -> Dict[str, Any]:
        """
        Get a knowledge document.

        Returns:
            Dictionary with 'title', 'content', 'category', etc.
        """
        safe_id = KnowledgeService._sanitize_knowledge_id(knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Knowledge document '{knowledge_id}' not found")

        content = file_path.read_text(encoding="utf-8")
        metadata, actual_content = KnowledgeService._parse_frontmatter(content)

        # Ensure knowledge_id is set
        if not metadata.get("id"):
            metadata["id"] = knowledge_id

        # Add actual content to metadata
        metadata["content"] = actual_content

        return metadata

    @staticmethod
    def list_all_knowledge() -> List[Dict[str, str]]:
        """
        List all knowledge documents.

        Returns:
            List of knowledge metadata dictionaries
        """
        knowledge_list = []

        for file_path in KNOWLEDGE_DIR.glob("*.md"):
            try:
                knowledge_id = file_path.stem
                metadata = KnowledgeService.get_knowledge(knowledge_id)
                knowledge_list.append(
                    {
                        "id": metadata.get("id", knowledge_id),
                        "title": metadata.get("title", knowledge_id),
                        "category": metadata.get("category", "note"),
                        "tags": metadata.get("tags", []),
                    }
                )
            except Exception:
                continue

        return knowledge_list
