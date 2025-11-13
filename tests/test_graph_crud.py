"""Tests for graph CRUD tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp import types

from skill_mcp.tools.graph_crud import (
    _query_related_skills,
    _query_dependency_tree,
    _query_skills_using_package,
    _query_circular_deps,
    _query_most_used_deps,
    _query_orphaned_skills,
    _query_complexity,
    _query_imports,
    _query_similar_skills,
    _query_conflicts,
    _query_execution_history,
    _query_neighborhood,
    _handle_sync,
    _handle_stats,
    _handle_query,
    GraphCrud,
)
from skill_mcp.models_crud import GraphCrudInput


class TestQueryHelperFunctions:
    """Test query helper functions that wrap GraphQueries."""

    def test_query_related_skills_with_skill_name(self):
        """Test _query_related_skills with skill name."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill",
            depth=2
        )

        result = _query_related_skills(input_data)

        assert result is not None
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_query_related_skills_without_skill_name(self):
        """Test _query_related_skills without skill name."""
        input_data = GraphCrudInput(operation="query")

        result = _query_related_skills(input_data)

        assert result is None

    def test_query_dependency_tree_with_skill_name(self):
        """Test _query_dependency_tree with skill name."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill"
        )

        result = _query_dependency_tree(input_data)

        assert result is not None
        assert "query" in result
        assert "params" in result

    def test_query_dependency_tree_without_skill_name(self):
        """Test _query_dependency_tree without skill name."""
        input_data = GraphCrudInput(operation="query")

        result = _query_dependency_tree(input_data)

        assert result is None

    def test_query_skills_using_package(self):
        """Test _query_skills_using_package."""
        input_data = GraphCrudInput(
            operation="query",
            package_name="requests"
        )

        result = _query_skills_using_package(input_data)

        assert result is not None
        assert "query" in result
        assert result["params"]["package_name"] == "requests"

    def test_query_circular_deps(self):
        """Test _query_circular_deps."""
        input_data = GraphCrudInput(operation="query")

        result = _query_circular_deps(input_data)

        assert result is not None
        assert "query" in result

    def test_query_most_used_deps(self):
        """Test _query_most_used_deps."""
        input_data = GraphCrudInput(
            operation="query",
            limit=10
        )

        result = _query_most_used_deps(input_data)

        assert result is not None
        assert "params" in result
        assert result["params"]["limit"] == 10

    def test_query_orphaned_skills(self):
        """Test _query_orphaned_skills."""
        input_data = GraphCrudInput(operation="query")

        result = _query_orphaned_skills(input_data)

        assert result is not None
        assert "query" in result

    def test_query_complexity(self):
        """Test _query_complexity."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill"
        )

        result = _query_complexity(input_data)

        assert result is not None
        assert result["params"]["skill_name"] == "test-skill"

    def test_query_imports(self):
        """Test _query_imports."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill"
        )

        result = _query_imports(input_data)

        assert result is not None
        assert result["params"]["skill_name"] == "test-skill"

    def test_query_similar_skills(self):
        """Test _query_similar_skills."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill",
            limit=5
        )

        result = _query_similar_skills(input_data)

        assert result is not None
        assert result["params"]["skill_name"] == "test-skill"
        assert result["params"]["limit"] == 5

    def test_query_conflicts(self):
        """Test _query_conflicts."""
        input_data = GraphCrudInput(operation="query")

        result = _query_conflicts(input_data)

        assert result is not None
        assert "query" in result

    def test_query_execution_history(self):
        """Test _query_execution_history."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill",
            limit=10
        )

        result = _query_execution_history(input_data)

        assert result is not None
        assert result["params"]["skill_name"] == "test-skill"

    def test_query_neighborhood(self):
        """Test _query_neighborhood."""
        input_data = GraphCrudInput(
            operation="query",
            skill_name="test-skill",
            depth=1
        )

        result = _query_neighborhood(input_data)

        assert result is not None
        assert result["params"]["skill_name"] == "test-skill"


class TestHandlerFunctions:
    """Test handler functions - simplified tests."""

    def test_handler_functions_exist(self):
        """Test that handler functions exist."""
        assert callable(_handle_sync)
        assert callable(_handle_stats)
        assert callable(_handle_query)

    @pytest.mark.asyncio
    async def test_handle_query_with_valid_query_type(self):
        """Test _handle_query with valid query type."""
        with patch("skill_mcp.tools.graph_crud.GRAPH_ENABLED", True):
            with patch("skill_mcp.tools.graph_crud.GraphService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.is_connected = MagicMock(return_value=True)
                mock_service.execute_query = AsyncMock(return_value=[
                    {"skill": "skill1", "description": "Desc 1"},
                    {"skill": "skill2", "description": "Desc 2"}
                ])
                mock_service_class.return_value = mock_service

                input_data = GraphCrudInput(
                    operation="query",
                    query_type="related_skills",
                    skill_name="test-skill"
                )

                result = await _handle_query(input_data)

                assert len(result) == 1
                mock_service.execute_query.assert_called_once()


class TestGraphCrudClass:
    """Test GraphCrud class - simplified."""

    def test_graph_crud_class_exists(self):
        """Test that GraphCrud class exists and can be instantiated."""
        crud = GraphCrud()
        assert crud is not None
        assert isinstance(crud, GraphCrud)
