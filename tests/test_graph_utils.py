"""Tests for graph utility functions."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from skill_mcp.utils.graph_utils import (
    get_current_timestamps,
    require_connection,
    auto_sync_skill_to_graph,
    auto_delete_skill_from_graph,
)


class TestGetCurrentTimestamps:
    """Test timestamp generation."""

    def test_returns_dict_with_required_keys(self):
        """Test that it returns a dict with created_at and updated_at."""
        result = get_current_timestamps()

        assert isinstance(result, dict)
        assert "created_at" in result
        assert "updated_at" in result

    def test_timestamps_are_iso_format(self):
        """Test that timestamps are in ISO format."""
        result = get_current_timestamps()

        # Should be parseable as ISO format
        datetime.fromisoformat(result["created_at"])
        datetime.fromisoformat(result["updated_at"])

    def test_timestamps_are_equal(self):
        """Test that created_at and updated_at are the same."""
        result = get_current_timestamps()

        assert result["created_at"] == result["updated_at"]

    def test_timestamps_are_recent(self):
        """Test that timestamps are current (within 1 second)."""
        before = datetime.now()
        result = get_current_timestamps()
        after = datetime.now()

        timestamp = datetime.fromisoformat(result["created_at"])

        assert before <= timestamp <= after


class TestRequireConnectionDecorator:
    """Test the require_connection decorator."""

    @pytest.mark.asyncio
    async def test_raises_error_when_not_connected(self):
        """Test that it raises GraphServiceError when not connected."""
        # Create a mock class with a method decorated with require_connection
        class MockService:
            def is_connected(self):
                return False

            @require_connection
            async def some_operation(self):
                return "success"

        service = MockService()

        from skill_mcp.services.graph_service import GraphServiceError
        with pytest.raises(GraphServiceError) as exc_info:
            await service.some_operation()

        assert "Not connected to Neo4j" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_executes_when_connected(self):
        """Test that it executes the function when connected."""
        class MockService:
            def is_connected(self):
                return True

            @require_connection
            async def some_operation(self):
                return "success"

        service = MockService()
        result = await service.some_operation()

        assert result == "success"

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        class MockService:
            def is_connected(self):
                return True

            @require_connection
            async def documented_function(self):
                """This is a documented function."""
                return "result"

        service = MockService()

        # Function name and docstring should be preserved
        assert service.documented_function.__name__ == "documented_function"
        assert service.documented_function.__doc__ == "This is a documented function."

    @pytest.mark.asyncio
    async def test_passes_arguments_correctly(self):
        """Test that decorator passes arguments to the wrapped function."""
        class MockService:
            def is_connected(self):
                return True

            @require_connection
            async def operation_with_args(self, arg1, arg2, kwarg1=None):
                return f"{arg1}-{arg2}-{kwarg1}"

        service = MockService()
        result = await service.operation_with_args("a", "b", kwarg1="c")

        assert result == "a-b-c"


class TestAutoSyncSkillToGraph:
    """Test auto_sync_skill_to_graph function."""

    @pytest.mark.asyncio
    async def test_returns_immediately_when_graph_disabled(self):
        """Test that it returns immediately when GRAPH_ENABLED is False."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", False):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                # Should not raise any errors or try to import GraphService
                await auto_sync_skill_to_graph("test-skill")

    @pytest.mark.asyncio
    async def test_returns_immediately_when_auto_sync_disabled(self):
        """Test that it returns immediately when GRAPH_AUTO_SYNC is False."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", False):
                # Should not raise any errors or try to import GraphService
                await auto_sync_skill_to_graph("test-skill")

    @pytest.mark.asyncio
    async def test_silently_fails_on_import_error(self):
        """Test that it silently fails if GraphService import fails."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", side_effect=ImportError("No module")):
                    # Should not raise the ImportError
                    await auto_sync_skill_to_graph("test-skill")

    @pytest.mark.asyncio
    async def test_calls_sync_skill_to_graph_when_enabled(self):
        """Test that it calls GraphService.sync_skill_to_graph when enabled."""
        mock_graph_service = MagicMock()
        mock_graph_service.sync_skill_to_graph = AsyncMock()

        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", return_value=mock_graph_service):
                    await auto_sync_skill_to_graph("test-skill")

                    mock_graph_service.sync_skill_to_graph.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_silently_fails_on_sync_error(self):
        """Test that it silently fails if sync_skill_to_graph raises an error."""
        mock_graph_service = MagicMock()
        mock_graph_service.sync_skill_to_graph = AsyncMock(
            side_effect=Exception("Sync failed")
        )

        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", return_value=mock_graph_service):
                    # Should not raise the exception
                    await auto_sync_skill_to_graph("test-skill")


class TestAutoDeleteSkillFromGraph:
    """Test auto_delete_skill_from_graph function."""

    @pytest.mark.asyncio
    async def test_returns_immediately_when_graph_disabled(self):
        """Test that it returns immediately when GRAPH_ENABLED is False."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", False):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                # Should not raise any errors or try to import GraphService
                await auto_delete_skill_from_graph("test-skill")

    @pytest.mark.asyncio
    async def test_returns_immediately_when_auto_sync_disabled(self):
        """Test that it returns immediately when GRAPH_AUTO_SYNC is False."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", False):
                # Should not raise any errors or try to import GraphService
                await auto_delete_skill_from_graph("test-skill")

    @pytest.mark.asyncio
    async def test_silently_fails_on_import_error(self):
        """Test that it silently fails if GraphService import fails."""
        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", side_effect=ImportError("No module")):
                    # Should not raise the ImportError
                    await auto_delete_skill_from_graph("test-skill")

    @pytest.mark.asyncio
    async def test_calls_delete_skill_from_graph_when_enabled(self):
        """Test that it calls GraphService.delete_skill_from_graph when enabled."""
        mock_graph_service = MagicMock()
        mock_graph_service.delete_skill_from_graph = AsyncMock()

        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", return_value=mock_graph_service):
                    await auto_delete_skill_from_graph("test-skill")

                    mock_graph_service.delete_skill_from_graph.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_silently_fails_on_delete_error(self):
        """Test that it silently fails if delete_skill_from_graph raises an error."""
        mock_graph_service = MagicMock()
        mock_graph_service.delete_skill_from_graph = AsyncMock(
            side_effect=Exception("Delete failed")
        )

        with patch("skill_mcp.utils.graph_utils.GRAPH_ENABLED", True):
            with patch("skill_mcp.utils.graph_utils.GRAPH_AUTO_SYNC", True):
                with patch("skill_mcp.services.graph_service.GraphService", return_value=mock_graph_service):
                    # Should not raise the exception
                    await auto_delete_skill_from_graph("test-skill")
