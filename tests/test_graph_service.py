"""Tests for graph service with mocked Neo4j."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from skill_mcp.services.graph_service import GraphService, GraphServiceError
from skill_mcp.models import Node, NodeType, Relationship, RelationshipType


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
    driver = MagicMock()
    session = MagicMock()
    result = MagicMock()

    # Setup session context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)

    # Setup result
    result.single = MagicMock(return_value=None)
    result.data = MagicMock(return_value=[])
    session.run = MagicMock(return_value=result)

    driver.session = MagicMock(return_value=session)
    driver.close = MagicMock()

    return driver, session, result


@pytest.fixture
def graph_service(mock_neo4j_driver):
    """Create graph service instance with mocked driver."""
    driver, session, result = mock_neo4j_driver

    # Reset singleton
    GraphService._instance = None
    GraphService._driver = None

    with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", True):
        with patch("skill_mcp.services.graph_service.GraphDatabase") as mock_gdb:
            mock_gdb.driver = MagicMock(return_value=driver)
            service = GraphService()
            yield service, driver, session, result

    # Cleanup
    GraphService._instance = None
    GraphService._driver = None


class TestGraphServiceInitialization:
    """Test graph service initialization and connection."""

    def test_singleton_pattern(self):
        """Test that GraphService follows singleton pattern."""
        # Reset singleton
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", True):
            with patch("skill_mcp.services.graph_service.GraphDatabase"):
                service1 = GraphService()
                service2 = GraphService()

                assert service1 is service2

    def test_initialization_when_graph_disabled(self):
        """Test that initialization does nothing when GRAPH_ENABLED is False."""
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", False):
            service = GraphService()
            assert GraphService._driver is None

    def test_initialization_without_neo4j_package(self):
        """Test error when neo4j package is not installed."""
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", True):
            with patch("skill_mcp.services.graph_service.GraphDatabase", None):
                with pytest.raises(GraphServiceError) as exc_info:
                    GraphService()

                assert "neo4j package not installed" in str(exc_info.value)

    def test_connect_success(self, mock_neo4j_driver):
        """Test successful connection to Neo4j."""
        driver, session, result = mock_neo4j_driver
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", True):
            with patch("skill_mcp.services.graph_service.GraphDatabase") as mock_gdb:
                mock_gdb.driver = MagicMock(return_value=driver)
                service = GraphService()

                assert GraphService._driver is not None
                mock_gdb.driver.assert_called_once()

    def test_connect_service_unavailable(self):
        """Test connection failure when Neo4j is unavailable."""
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", True):
            with patch("skill_mcp.services.graph_service.GraphDatabase") as mock_gdb:
                from skill_mcp.services.graph_service import ServiceUnavailable

                mock_gdb.driver = MagicMock(
                    side_effect=ServiceUnavailable("Connection refused")
                )

                with pytest.raises(GraphServiceError) as exc_info:
                    GraphService()

                assert "Cannot connect to Neo4j" in str(exc_info.value)

    def test_close_connection(self, graph_service):
        """Test closing Neo4j connection."""
        service, driver, session, result = graph_service

        service.close()

        driver.close.assert_called_once()
        assert GraphService._driver is None

    def test_is_connected_when_connected(self, graph_service):
        """Test is_connected returns True when connected."""
        service, driver, session, result = graph_service

        assert service.is_connected() is True

    def test_is_connected_when_graph_disabled(self):
        """Test is_connected returns False when GRAPH_ENABLED is False."""
        GraphService._instance = None
        GraphService._driver = MagicMock()

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", False):
            service = GraphService()
            assert service.is_connected() is False

    def test_is_connected_when_no_driver(self):
        """Test is_connected returns False when no driver."""
        GraphService._instance = None
        GraphService._driver = None

        with patch("skill_mcp.services.graph_service.GRAPH_ENABLED", False):
            service = GraphService()
            assert service.is_connected() is False

    def test_is_connected_when_connection_fails(self, graph_service):
        """Test is_connected returns False on connection error."""
        service, driver, session, result = graph_service

        session.run = MagicMock(side_effect=Exception("Connection error"))

        assert service.is_connected() is False


class TestGenericNodeOperations:
    """Test generic node CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_node_skill(self, graph_service):
        """Test creating a Skill node."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(
            return_value={"id": "skill-abc123", "name": "test-skill", "type": "Skill"}
        )
        result.single = MagicMock(return_value=mock_record)

        node = Node(
            id="skill-abc123",
            type=NodeType.SKILL,
            name="test-skill",
            properties={"skill_path": "/path/to/skill"},
        )

        created = await service.create_node(node)

        assert created["id"] == "skill-abc123"
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_get_node(self, graph_service):
        """Test getting a node by ID."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(
            return_value={"id": "skill-123", "name": "test-skill", "type": "Skill"}
        )
        result.single = MagicMock(return_value=mock_record)

        node = await service.get_node("skill-123")

        assert node is not None
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_update_node(self, graph_service):
        """Test updating a node."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(
            return_value={"id": "skill-123", "name": "updated-skill"}
        )
        result.single = MagicMock(return_value=mock_record)

        updated = await service.update_node("skill-123", {"name": "updated-skill"})

        assert updated is not None
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_delete_node(self, graph_service):
        """Test deleting a node."""
        service, driver, session, result = graph_service

        await service.delete_node("skill-123")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_list_nodes(self, graph_service):
        """Test listing nodes."""
        service, driver, session, result = graph_service

        # Mock the result
        result.data = MagicMock(
            return_value=[
                {"id": "skill-1", "name": "skill1", "type": "Skill"},
                {"id": "skill-2", "name": "skill2", "type": "Skill"},
            ]
        )

        nodes = await service.list_nodes(node_type=NodeType.SKILL)

        assert len(nodes) == 2
        session.run.assert_called()


class TestGenericRelationshipOperations:
    """Test generic relationship CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_relationship(self, graph_service):
        """Test creating a relationship."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(return_value={"type": "CONTAINS"})
        result.single = MagicMock(return_value=mock_record)

        rel = Relationship(
            from_id="skill-1", to_id="script-1", type=RelationshipType.CONTAINS
        )

        created = await service.create_relationship(rel)

        assert created is not None
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_get_relationships(self, graph_service):
        """Test getting relationships for a node."""
        service, driver, session, result = graph_service

        # Mock the result
        result.data = MagicMock(
            return_value=[
                {
                    "type": "CONTAINS",
                    "other_node": {
                        "id": "script-1",
                        "name": "test.py",
                        "type": "Script",
                    },
                }
            ]
        )

        rels = await service.get_relationships("skill-1")

        assert len(rels) == 1
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_delete_relationship(self, graph_service):
        """Test deleting a relationship."""
        service, driver, session, result = graph_service

        await service.delete_relationship(
            "skill-1", "script-1", RelationshipType.CONTAINS
        )

        session.run.assert_called()


class TestQueryOperations:
    """Test query and traversal operations."""

    @pytest.mark.asyncio
    async def test_query_cypher(self, graph_service):
        """Test executing raw Cypher query."""
        service, driver, session, result = graph_service

        # Mock the result
        result.data = MagicMock(
            return_value=[
                {"name": "skill1"},
                {"name": "skill2"},
            ]
        )

        results = await service.query_cypher("MATCH (n:Skill) RETURN n.name")

        assert len(results) == 2
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_traverse_graph(self, graph_service):
        """Test graph traversal."""
        service, driver, session, result = graph_service

        # Mock the result
        result.data = MagicMock(
            return_value=[
                {
                    "nodes": [
                        {"id": "skill-1", "name": "skill1", "type": "Skill"},
                        {"id": "script-1", "name": "test.py", "type": "Script"},
                    ],
                    "relationships": [{"type": "CONTAINS"}],
                }
            ]
        )

        traversal = await service.traverse_graph("skill-1", max_depth=2)

        assert "nodes" in traversal or traversal is not None
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_find_path(self, graph_service):
        """Test pathfinding."""
        service, driver, session, result = graph_service

        # Mock the result
        result.data = MagicMock(return_value=[])

        paths = await service.find_path("skill-1", "script-1")

        assert isinstance(paths, list)
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_get_graph_stats(self, graph_service):
        """Test getting graph statistics."""
        service, driver, session, result = graph_service

        # Mock the result with multiple queries
        result.data = MagicMock(
            side_effect=[
                [{"count": 10}],  # total nodes
                [{"count": 15}],  # total relationships
                [
                    {"type": "Skill", "count": 5},
                    {"type": "Script", "count": 5},
                ],  # node counts
                [{"type": "CONTAINS", "count": 10}],  # relationship counts
            ]
        )

        stats = await service.get_graph_stats()

        assert "total_nodes" in stats
        assert "total_relationships" in stats
        session.run.assert_called()


class TestHelperMethods:
    """Test helper methods."""

    def test_helper_methods_exist(self, graph_service):
        """Test that new generic methods exist."""
        service, driver, session, result = graph_service

        # Test new generic methods exist
        assert hasattr(service, "create_node")
        assert hasattr(service, "get_node")
        assert hasattr(service, "update_node")
        assert hasattr(service, "delete_node")
        assert hasattr(service, "list_nodes")
        assert hasattr(service, "create_relationship")
        assert hasattr(service, "get_relationships")
        assert hasattr(service, "delete_relationship")
        assert hasattr(service, "query_cypher")
        assert hasattr(service, "traverse_graph")
        assert hasattr(service, "find_path")
        assert hasattr(service, "get_graph_stats")
