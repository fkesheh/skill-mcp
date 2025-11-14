"""Tests for graph node and relationship models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from skill_mcp.models import Node, NodeType, Relationship, RelationshipType


class TestNodeType:
    """Tests for NodeType enum."""

    def test_node_types_exist(self):
        """Test all expected node types exist."""
        assert NodeType.SKILL == "Skill"
        assert NodeType.KNOWLEDGE == "Knowledge"
        assert NodeType.SCRIPT == "Script"
        assert NodeType.TOOL == "Tool"

    def test_node_type_values(self):
        """Test node type values are correct."""
        assert NodeType.SKILL.value == "Skill"
        assert NodeType.KNOWLEDGE.value == "Knowledge"
        assert NodeType.SCRIPT.value == "Script"
        assert NodeType.TOOL.value == "Tool"


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_relationship_types_exist(self):
        """Test all expected relationship types exist."""
        assert RelationshipType.CONTAINS == "CONTAINS"
        assert RelationshipType.DEPENDS_ON == "DEPENDS_ON"
        assert RelationshipType.USES == "USES"
        assert RelationshipType.REFERENCES == "REFERENCES"
        assert RelationshipType.RELATED_TO == "RELATED_TO"
        assert RelationshipType.EXPLAINS == "EXPLAINS"
        assert RelationshipType.IMPORTS == "IMPORTS"

    def test_relationship_type_values(self):
        """Test relationship type values are correct."""
        assert RelationshipType.CONTAINS.value == "CONTAINS"
        assert RelationshipType.DEPENDS_ON.value == "DEPENDS_ON"
        assert RelationshipType.USES.value == "USES"
        assert RelationshipType.REFERENCES.value == "REFERENCES"
        assert RelationshipType.RELATED_TO.value == "RELATED_TO"
        assert RelationshipType.EXPLAINS.value == "EXPLAINS"
        assert RelationshipType.IMPORTS.value == "IMPORTS"


class TestNode:
    """Tests for Node model."""

    def test_create_minimal_node(self):
        """Test creating a node with minimal required fields."""
        node = Node(
            id="test-123",
            type=NodeType.SKILL,
            name="test-skill",
        )

        assert node.id == "test-123"
        assert node.type == NodeType.SKILL
        assert node.name == "test-skill"
        assert node.description is None
        assert node.tags == []
        assert node.properties == {}
        assert isinstance(node.created_at, datetime)
        assert isinstance(node.updated_at, datetime)

    def test_create_full_node(self):
        """Test creating a node with all fields."""
        created = datetime.now()
        updated = datetime.now()

        node = Node(
            id="skill-abc123",
            type=NodeType.SKILL,
            name="web-scraper",
            description="A web scraping utility",
            tags=["web", "scraping", "data"],
            properties={
                "skill_path": "/path/to/skill",
                "has_env_file": True,
                "custom_field": "value",
            },
            created_at=created,
            updated_at=updated,
        )

        assert node.id == "skill-abc123"
        assert node.type == NodeType.SKILL
        assert node.name == "web-scraper"
        assert node.description == "A web scraping utility"
        assert node.tags == ["web", "scraping", "data"]
        assert node.properties == {
            "skill_path": "/path/to/skill",
            "has_env_file": True,
            "custom_field": "value",
        }
        assert node.created_at == created
        assert node.updated_at == updated

    def test_create_script_node(self):
        """Test creating a Script node with type-specific properties."""
        node = Node(
            id="script-xyz789",
            type=NodeType.SCRIPT,
            name="main.py",
            description="Main script",
            tags=["python"],
            properties={
                "language": "python",
                "file_path": "/path/to/main.py",
                "is_executable": True,
                "has_pep723": False,
            },
        )

        assert node.type == NodeType.SCRIPT
        assert node.properties["language"] == "python"
        assert node.properties["is_executable"] is True

    def test_create_knowledge_node(self):
        """Test creating a Knowledge node with type-specific properties."""
        node = Node(
            id="knowledge-def456",
            type=NodeType.KNOWLEDGE,
            name="Tutorial: Web Scraping",
            description="How to scrape websites",
            tags=["tutorial", "web"],
            properties={
                "category": "tutorial",
                "author": "John Doe",
                "content_path": "/path/to/tutorial.md",
            },
        )

        assert node.type == NodeType.KNOWLEDGE
        assert node.properties["category"] == "tutorial"
        assert node.properties["author"] == "John Doe"

    def test_create_tool_node(self):
        """Test creating a Tool node with type-specific properties."""
        node = Node(
            id="tool-mno123",
            type=NodeType.TOOL,
            name="web_fetch",
            description="Fetch web content",
            properties={
                "mcp_server": "web-tools",
                "tool_name": "web_fetch",
                "input_schema": {"url": "string"},
            },
        )

        assert node.type == NodeType.TOOL
        assert node.properties["mcp_server"] == "web-tools"
        assert node.properties["tool_name"] == "web_fetch"

    def test_node_validation_missing_required_fields(self):
        """Test that node creation fails without required fields."""
        with pytest.raises(ValidationError):
            Node()  # Missing all required fields

        with pytest.raises(ValidationError):
            Node(id="test-123")  # Missing type and name

        with pytest.raises(ValidationError):
            Node(id="test-123", type=NodeType.SKILL)  # Missing name

    def test_node_validation_invalid_type(self):
        """Test that node creation fails with invalid type."""
        with pytest.raises(ValidationError):
            Node(
                id="test-123",
                type="InvalidType",  # Not a valid NodeType
                name="test",
            )

    def test_node_serialization(self):
        """Test that node can be serialized to dict."""
        node = Node(
            id="test-123",
            type=NodeType.SKILL,
            name="test-skill",
            tags=["tag1", "tag2"],
            properties={"key": "value"},
        )

        data = node.model_dump()

        assert data["id"] == "test-123"
        assert data["type"] == "Skill"
        assert data["name"] == "test-skill"
        assert data["tags"] == ["tag1", "tag2"]
        assert data["properties"] == {"key": "value"}
        assert "created_at" in data
        assert "updated_at" in data


class TestRelationship:
    """Tests for Relationship model."""

    def test_create_minimal_relationship(self):
        """Test creating a relationship with minimal required fields."""
        rel = Relationship(
            from_id="node-1",
            to_id="node-2",
            type=RelationshipType.CONTAINS,
        )

        assert rel.from_id == "node-1"
        assert rel.to_id == "node-2"
        assert rel.type == RelationshipType.CONTAINS
        assert rel.properties == {}
        assert isinstance(rel.created_at, datetime)

    def test_create_full_relationship(self):
        """Test creating a relationship with all fields."""
        created = datetime.now()

        rel = Relationship(
            from_id="skill-abc123",
            to_id="script-def456",
            type=RelationshipType.CONTAINS,
            properties={
                "order": 1,
                "importance": "high",
            },
            created_at=created,
        )

        assert rel.from_id == "skill-abc123"
        assert rel.to_id == "script-def456"
        assert rel.type == RelationshipType.CONTAINS
        assert rel.properties == {"order": 1, "importance": "high"}
        assert rel.created_at == created

    def test_create_depends_on_relationship(self):
        """Test creating a DEPENDS_ON relationship."""
        rel = Relationship(
            from_id="script-1",
            to_id="script-2",
            type=RelationshipType.DEPENDS_ON,
            properties={
                "reason": "imports helper functions",
            },
        )

        assert rel.type == RelationshipType.DEPENDS_ON
        assert rel.properties["reason"] == "imports helper functions"

    def test_create_explains_relationship(self):
        """Test creating an EXPLAINS relationship."""
        rel = Relationship(
            from_id="knowledge-doc",
            to_id="skill-123",
            type=RelationshipType.EXPLAINS,
        )

        assert rel.type == RelationshipType.EXPLAINS

    def test_relationship_validation_missing_required_fields(self):
        """Test that relationship creation fails without required fields."""
        with pytest.raises(ValidationError):
            Relationship()  # Missing all required fields

        with pytest.raises(ValidationError):
            Relationship(from_id="node-1")  # Missing to_id and type

        with pytest.raises(ValidationError):
            Relationship(from_id="node-1", to_id="node-2")  # Missing type

    def test_relationship_validation_invalid_type(self):
        """Test that relationship creation fails with invalid type."""
        with pytest.raises(ValidationError):
            Relationship(
                from_id="node-1",
                to_id="node-2",
                type="INVALID_TYPE",  # Not a valid RelationshipType
            )

    def test_relationship_serialization(self):
        """Test that relationship can be serialized to dict."""
        rel = Relationship(
            from_id="node-1",
            to_id="node-2",
            type=RelationshipType.USES,
            properties={"frequency": "often"},
        )

        data = rel.model_dump()

        assert data["from_id"] == "node-1"
        assert data["to_id"] == "node-2"
        assert data["type"] == "USES"
        assert data["properties"] == {"frequency": "often"}
        assert "created_at" in data

    def test_bidirectional_relationships(self):
        """Test creating bidirectional relationships."""
        # Forward: Skill CONTAINS Script
        forward = Relationship(
            from_id="skill-1",
            to_id="script-1",
            type=RelationshipType.CONTAINS,
        )

        # Reverse could be: Script REFERENCES Skill
        reverse = Relationship(
            from_id="script-1",
            to_id="skill-1",
            type=RelationshipType.REFERENCES,
        )

        assert forward.from_id == reverse.to_id
        assert forward.to_id == reverse.from_id
