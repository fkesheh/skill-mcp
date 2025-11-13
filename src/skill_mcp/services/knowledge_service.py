"""Knowledge document management service."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from skill_mcp.core.config import KNOWLEDGE_DIR


class KnowledgeService:
    """Service for managing knowledge documents."""

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
        # Sanitize knowledge_id for filename
        safe_id = re.sub(r'[^\w\-]', '_', knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        # Create markdown with frontmatter
        frontmatter = f"""---
id: {knowledge_id}
title: {title}
category: {category}
tags: {', '.join(tags or [])}
author: {author or 'Unknown'}
---

"""
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
        safe_id = re.sub(r'[^\w\-]', '_', knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Knowledge document '{knowledge_id}' not found")

        # Preserve frontmatter, update title and content
        existing_content = file_path.read_text(encoding="utf-8")

        # Extract frontmatter
        if existing_content.startswith("---"):
            parts = existing_content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_lines = parts[1].strip().split("\n")
                # Update title in frontmatter
                new_frontmatter = []
                for line in frontmatter_lines:
                    if line.startswith("title:"):
                        new_frontmatter.append(f"title: {title}")
                    else:
                        new_frontmatter.append(line)

                full_content = f"---\n{chr(10).join(new_frontmatter)}\n---\n\n{content}"
            else:
                full_content = content
        else:
            full_content = content

        file_path.write_text(full_content, encoding="utf-8")
        return file_path

    @staticmethod
    def delete_knowledge(knowledge_id: str) -> None:
        """Delete a knowledge document."""
        safe_id = re.sub(r'[^\w\-]', '_', knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if file_path.exists():
            file_path.unlink()

    @staticmethod
    def get_knowledge(knowledge_id: str) -> Dict[str, str]:
        """
        Get a knowledge document.

        Returns:
            Dictionary with 'title', 'content', 'category', etc.
        """
        safe_id = re.sub(r'[^\w\-]', '_', knowledge_id)
        file_path = KNOWLEDGE_DIR / f"{safe_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Knowledge document '{knowledge_id}' not found")

        content = file_path.read_text(encoding="utf-8")

        # Parse frontmatter
        metadata = {
            "id": knowledge_id,
            "title": knowledge_id,
            "category": "note",
            "tags": [],
            "author": "Unknown",
            "content": content,
        }

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                actual_content = parts[2].strip()

                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        if key == "tags":
                            metadata["tags"] = [t.strip() for t in value.split(",")]
                        else:
                            metadata[key] = value

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
