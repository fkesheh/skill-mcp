"""Tests for relationship_crud tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp import types

from skill_mcp.models import RelationshipType
from skill_mcp.models_crud import RelationshipCrudInput
from skill_mcp.services.graph_service import GraphServiceError
from skill_mcp.tools.relationship_crud import RelationshipCrud


@pytest.fixture
def mock_graph_service():
    """Mock GraphService for testing."""
    with patch("skill_mcp.tools.relationship_crud.GRAPH_ENABLED", True):
        with patch("skill_mcp.tools.relationship_crud.GraphService") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance


class TestRelationshipCrudCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_contains_relationship(self, mock_graph_service):
        """Test creating a CONTAINS relationship."""
        rel_data = {
            "from_id": "skill-1",
            "to_id": "script-1",
            "type": "CONTAINS",
        }
        mock_graph_service.create_relationship = AsyncMock(return_value=rel_data)

        input_data = RelationshipCrudInput(
            operation="create",
            from_id="skill-1",
            to_id="script-1",
            relationship_type=RelationshipType.CONTAINS,
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text
        assert "CONTAINS" in result[0].text

    @pytest.mark.asyncio
    async def test_create_with_properties(self, mock_graph_service):
        """Test creating a relationship with properties."""
        rel_data = {
            "from_id": "script-1",
            "to_id": "script-2",
            "type": "DEPENDS_ON",
            "properties": {"reason": "test"},
        }
        mock_graph_service.create_relationship = AsyncMock(return_value=rel_data)

        input_data = RelationshipCrudInput(
            operation="create",
            from_id="script-1",
            to_id="script-2",
            relationship_type=RelationshipType.DEPENDS_ON,
            properties={"reason": "test"},
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_create_missing_from_id(self, mock_graph_service):
        """Test create fails without from_id."""
        input_data = RelationshipCrudInput(
            operation="create",
            to_id="script-1",
            relationship_type=RelationshipType.CONTAINS,
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "from_id" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_create_error_handling(self, mock_graph_service):
        """Test create error handling."""
        mock_graph_service.create_relationship = AsyncMock(side_effect=GraphServiceError("Failed"))

        input_data = RelationshipCrudInput(
            operation="create",
            from_id="skill-1",
            to_id="script-1",
            relationship_type=RelationshipType.CONTAINS,
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "Error" in result[0].text


class TestRelationshipCrudGet:
    """Tests for get operation."""

    @pytest.mark.asyncio
    async def test_get_relationships_for_node(self, mock_graph_service):
        """Test getting relationships for a node."""
        rels = [
            {
                "type": "CONTAINS",
                "other_node": {"id": "script-1", "name": "test.py", "type": "Script"},
                "direction": "outgoing",
            }
        ]
        mock_graph_service.get_relationships = AsyncMock(return_value=rels)

        input_data = RelationshipCrudInput(
            operation="get",
            node_id="skill-1",
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "CONTAINS" in result[0].text

    @pytest.mark.asyncio
    async def test_get_no_relationships(self, mock_graph_service):
        """Test getting relationships when none exist."""
        mock_graph_service.get_relationships = AsyncMock(return_value=[])

        input_data = RelationshipCrudInput(
            operation="get",
            node_id="skill-1",
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "No relationships" in result[0].text

    @pytest.mark.asyncio
    async def test_get_missing_node_id(self, mock_graph_service):
        """Test get fails without node_id."""
        input_data = RelationshipCrudInput(
            operation="get",
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "node_id" in result[0].text.lower()


class TestRelationshipCrudDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_relationship(self, mock_graph_service):
        """Test deleting a relationship."""
        mock_graph_service.delete_relationship = AsyncMock()

        input_data = RelationshipCrudInput(
            operation="delete",
            from_id="skill-1",
            to_id="script-1",
            relationship_type=RelationshipType.CONTAINS,
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "Deleted" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_missing_required_fields(self, mock_graph_service):
        """Test delete fails without required fields."""
        input_data = RelationshipCrudInput(
            operation="delete",
            from_id="skill-1",
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "required" in result[0].text.lower()


class TestRelationshipCrudList:
    """Tests for list operation."""

    @pytest.mark.asyncio
    async def test_list_relationships(self, mock_graph_service):
        """Test listing relationships."""
        rels = [
            {
                "type": "CONTAINS",
                "from_node": {"id": "skill-1", "name": "skill", "type": "Skill"},
                "to_node": {"id": "script-1", "name": "test.py", "type": "Script"},
            }
        ]
        mock_graph_service.list_relationships = AsyncMock(return_value=rels)

        input_data = RelationshipCrudInput(
            operation="list",
        )

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "CONTAINS" in result[0].text


class TestRelationshipCrudGeneral:
    """General tests."""

    @pytest.mark.asyncio
    @patch("skill_mcp.tools.relationship_crud.GRAPH_ENABLED", False)
    async def test_graph_disabled(self):
        """Test error when graph is disabled."""
        input_data = RelationshipCrudInput(operation="list")

        result = await RelationshipCrud.relationship_crud(input_data)

        assert len(result) == 1
        assert "not enabled" in result[0].text.lower()

    def test_tool_definition(self):
        """Test get_tool_definition."""
        tools = RelationshipCrud.get_tool_definition()

        assert len(tools) == 1
        assert tools[0].name == "relationship_crud"
