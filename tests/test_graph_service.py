"""Tests for graph service with mocked Neo4j."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from pathlib import Path

from skill_mcp.services.graph_service import GraphService, GraphServiceError
from skill_mcp.models import SkillDetails, FileInfo, ScriptInfo


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
                mock_gdb.driver = MagicMock(side_effect=ServiceUnavailable("Connection refused"))

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


class TestGraphServiceHelperMethods:
    """Test helper methods - simplified tests."""

    def test_helper_methods_exist(self, graph_service):
        """Test that helper methods exist."""
        service, driver, session, result = graph_service

        assert hasattr(service, '_execute_single_result_query')
        assert hasattr(service, '_execute_write_query')
        assert callable(service._execute_single_result_query)
        assert callable(service._execute_write_query)


class TestGraphServiceNodeOperations:
    """Test node creation operations - simplified."""

    @pytest.mark.asyncio
    async def test_node_creation_methods_exist(self, graph_service):
        """Test that node creation methods exist."""
        service, driver, session, result = graph_service

        # Verify methods exist
        assert hasattr(service, 'create_skill_node')
        assert hasattr(service, 'create_file_node')
        assert hasattr(service, 'create_dependency_node')
        assert hasattr(service, 'create_env_var_node')
        assert hasattr(service, 'create_knowledge_node')

    @pytest.mark.asyncio
    async def test_create_dependency_node(self, graph_service):
        """Test dependency node creation."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(return_value={
            "package_name": "requests",
            "ecosystem": "pypi",
            "version_spec": ">=2.28.0"
        })
        result.single = MagicMock(return_value=mock_record)

        node = await service.create_dependency_node("requests", "pypi", ">=2.28.0")

        assert node["package_name"] == "requests"
        assert node["ecosystem"] == "pypi"
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_create_env_var_node(self, graph_service):
        """Test environment variable node creation."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(return_value={
            "key": "API_KEY",
            "skill_name": "test-skill"
        })
        result.single = MagicMock(return_value=mock_record)

        node = await service.create_env_var_node("test-skill", "API_KEY")

        assert node["key"] == "API_KEY"
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_create_knowledge_node(self, graph_service):
        """Test knowledge node creation."""
        service, driver, session, result = graph_service

        # Mock the result
        mock_record = MagicMock()
        mock_record.__getitem__ = MagicMock(return_value={
            "id": "test-knowledge",
            "title": "Test Knowledge",
            "category": "tutorial"
        })
        result.single = MagicMock(return_value=mock_record)

        node = await service.create_knowledge_node(
            knowledge_id="test-knowledge",
            title="Test Knowledge",
            content="Test content",
            category="tutorial",
            tags=["python"],
            author="Test Author"
        )

        assert node["id"] == "test-knowledge"
        assert node["title"] == "Test Knowledge"
        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_delete_knowledge_node(self, graph_service):
        """Test knowledge node deletion."""
        service, driver, session, result = graph_service

        await service.delete_knowledge_node("test-knowledge")

        session.run.assert_called()


class TestGraphServiceLinkOperations:
    """Test relationship creation operations."""

    @pytest.mark.asyncio
    async def test_link_skill_to_file(self, graph_service):
        """Test linking skill to file."""
        service, driver, session, result = graph_service

        await service.link_skill_to_file("test-skill", "test.py")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_link_file_to_dependency(self, graph_service):
        """Test linking file to dependency."""
        service, driver, session, result = graph_service

        await service.link_file_to_dependency("test-skill", "test.py", "requests", "pypi")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_link_skill_to_env_var(self, graph_service):
        """Test linking skill to environment variable."""
        service, driver, session, result = graph_service

        await service.link_skill_to_env_var("test-skill", "API_KEY")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_link_knowledge_to_skill(self, graph_service):
        """Test linking knowledge to skill."""
        service, driver, session, result = graph_service

        await service.link_knowledge_to_skill("test-knowledge", "test-skill", "EXPLAINS")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_link_knowledge_to_knowledge(self, graph_service):
        """Test linking knowledge to knowledge."""
        service, driver, session, result = graph_service

        await service.link_knowledge_to_knowledge("knowledge1", "knowledge2")

        session.run.assert_called()


class TestGraphServiceMainOperations:
    """Test main graph operations - simplified."""

    @pytest.mark.asyncio
    async def test_delete_skill_from_graph(self, graph_service):
        """Test deleting skill from graph."""
        service, driver, session, result = graph_service

        await service.delete_skill_from_graph("test-skill")

        session.run.assert_called()

    @pytest.mark.asyncio
    async def test_execute_query_methods_exist(self, graph_service):
        """Test that query execution methods exist."""
        service, driver, session, result = graph_service

        assert hasattr(service, 'execute_query')
        assert hasattr(service, 'get_graph_stats')
        assert callable(service.execute_query)
        assert callable(service.get_graph_stats)
