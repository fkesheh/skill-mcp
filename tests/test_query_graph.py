"""Tests for query_graph tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp import types

from skill_mcp.models import NodeType, RelationshipType
from skill_mcp.models_crud import QueryGraphInput
from skill_mcp.services.graph_service import GraphServiceError
from skill_mcp.tools.query_graph import QueryGraph


@pytest.fixture
def mock_graph_service():
    """Mock GraphService for testing."""
    with patch("skill_mcp.tools.query_graph.GRAPH_ENABLED", True):
        with patch("skill_mcp.tools.query_graph.GraphService") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance


class TestQueryGraphQuery:
    """Tests for query operation."""

    @pytest.mark.asyncio
    async def test_execute_cypher_query(self, mock_graph_service):
        """Test executing a Cypher query."""
        results = [
            {"name": "skill1", "id": "skill-1"},
            {"name": "skill2", "id": "skill-2"},
        ]
        mock_graph_service.query_cypher = AsyncMock(return_value=results)

        input_data = QueryGraphInput(
            operation="query",
            cypher_query="MATCH (n:Skill) RETURN n.name, n.id",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "Query Results" in result[0].text or "rows" in result[0].text

    @pytest.mark.asyncio
    async def test_query_with_parameters(self, mock_graph_service):
        """Test query with parameters."""
        results = [{"name": "test-skill"}]
        mock_graph_service.query_cypher = AsyncMock(return_value=results)

        input_data = QueryGraphInput(
            operation="query",
            cypher_query="MATCH (n:Skill {name: $name}) RETURN n",
            params={"name": "test-skill"},
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_no_results(self, mock_graph_service):
        """Test query with no results."""
        mock_graph_service.query_cypher = AsyncMock(return_value=[])

        input_data = QueryGraphInput(
            operation="query",
            cypher_query="MATCH (n:NonExistent) RETURN n",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "no results" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_query_missing_cypher(self, mock_graph_service):
        """Test query fails without cypher_query."""
        input_data = QueryGraphInput(
            operation="query",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "required" in result[0].text.lower()


class TestQueryGraphTraverse:
    """Tests for traverse operation."""

    @pytest.mark.asyncio
    async def test_traverse_from_node(self, mock_graph_service):
        """Test traversing from a starting node."""
        traverse_result = {
            "nodes": [
                {"id": "skill-1", "name": "skill1", "type": "Skill"},
                {"id": "script-1", "name": "test.py", "type": "Script"},
            ],
            "relationships": [{"type": "CONTAINS", "from_id": "skill-1", "to_id": "script-1"}],
        }
        mock_graph_service.traverse_graph = AsyncMock(return_value=traverse_result)

        input_data = QueryGraphInput(
            operation="traverse",
            start_node_id="skill-1",
            max_depth=2,
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "Traversal" in result[0].text or "Nodes found" in result[0].text

    @pytest.mark.asyncio
    async def test_traverse_with_filters(self, mock_graph_service):
        """Test traverse with filters."""
        traverse_result = {
            "nodes": [{"id": "script-1", "name": "test.py", "type": "Script"}],
            "relationships": [],
        }
        mock_graph_service.traverse_graph = AsyncMock(return_value=traverse_result)

        input_data = QueryGraphInput(
            operation="traverse",
            start_node_id="skill-1",
            node_types=[NodeType.SCRIPT],
            relationship_types=[RelationshipType.CONTAINS],
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_traverse_no_results(self, mock_graph_service):
        """Test traverse with no results."""
        traverse_result = {"nodes": [], "relationships": []}
        mock_graph_service.traverse_graph = AsyncMock(return_value=traverse_result)

        input_data = QueryGraphInput(
            operation="traverse",
            start_node_id="skill-1",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "No connected nodes" in result[0].text or "No" in result[0].text

    @pytest.mark.asyncio
    async def test_traverse_missing_start_node(self, mock_graph_service):
        """Test traverse fails without start_node_id."""
        input_data = QueryGraphInput(
            operation="traverse",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "required" in result[0].text.lower()


class TestQueryGraphFindPath:
    """Tests for find_path operation."""

    @pytest.mark.asyncio
    async def test_find_path_between_nodes(self, mock_graph_service):
        """Test finding path between nodes."""
        paths = [
            {
                "nodes": [
                    {"id": "skill-1", "name": "skill", "type": "Skill"},
                    {"id": "script-1", "name": "test.py", "type": "Script"},
                ],
                "relationships": [{"type": "CONTAINS", "from_id": "skill-1", "to_id": "script-1"}],
            }
        ]
        mock_graph_service.find_path = AsyncMock(return_value=paths)

        input_data = QueryGraphInput(
            operation="find_path",
            from_id="skill-1",
            to_id="script-1",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "Path" in result[0].text

    @pytest.mark.asyncio
    async def test_find_path_no_path(self, mock_graph_service):
        """Test when no path exists."""
        mock_graph_service.find_path = AsyncMock(return_value=[])

        input_data = QueryGraphInput(
            operation="find_path",
            from_id="skill-1",
            to_id="skill-2",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "No path" in result[0].text

    @pytest.mark.asyncio
    async def test_find_path_missing_from_id(self, mock_graph_service):
        """Test find_path fails without from_id."""
        input_data = QueryGraphInput(
            operation="find_path",
            to_id="skill-2",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "required" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_find_path_missing_to_id(self, mock_graph_service):
        """Test find_path fails without to_id."""
        input_data = QueryGraphInput(
            operation="find_path",
            from_id="skill-1",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "required" in result[0].text.lower()


class TestQueryGraphStats:
    """Tests for stats operation."""

    @pytest.mark.asyncio
    async def test_get_graph_stats(self, mock_graph_service):
        """Test getting graph statistics."""
        stats = {
            "total_nodes": 10,
            "total_relationships": 15,
            "node_counts": {"Skill": 5, "Script": 5},
            "relationship_counts": {"CONTAINS": 10, "DEPENDS_ON": 5},
        }
        mock_graph_service.get_graph_stats = AsyncMock(return_value=stats)

        input_data = QueryGraphInput(
            operation="stats",
        )

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "Statistics" in result[0].text
        assert "10" in result[0].text  # total nodes


class TestQueryGraphGeneral:
    """General tests."""

    @pytest.mark.asyncio
    @patch("skill_mcp.tools.query_graph.GRAPH_ENABLED", False)
    async def test_graph_disabled(self):
        """Test error when graph is disabled."""
        input_data = QueryGraphInput(operation="stats")

        result = await QueryGraph.query_graph(input_data)

        assert len(result) == 1
        assert "not enabled" in result[0].text.lower()

    def test_tool_definition(self):
        """Test get_tool_definition."""
        tools = QueryGraph.get_tool_definition()

        assert len(tools) == 1
        assert tools[0].name == "query_graph"
