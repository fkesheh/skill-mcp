"""Tests for node_crud tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp import types

from skill_mcp.models import NodeType
from skill_mcp.models_crud import NodeCrudInput
from skill_mcp.services.graph_service import GraphServiceError
from skill_mcp.tools.node_crud import NodeCrud


@pytest.fixture
def mock_graph_service():
    """Mock GraphService for testing."""
    with patch("skill_mcp.tools.node_crud.GRAPH_ENABLED", True):
        with patch("skill_mcp.tools.node_crud.GraphService") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance


@pytest.fixture
def sample_node_data():
    """Sample node data for testing."""
    return {
        "id": "skill-abc123",
        "type": "Skill",
        "name": "web-scraper",
        "description": "Web scraping utility",
        "tags": ["web", "scraping"],
        "properties": {
            "skill_path": "/path/to/skill",
            "has_env_file": True,
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


class TestNodeCrudCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_skill_node(self, mock_graph_service, sample_node_data):
        """Test creating a Skill node."""
        mock_graph_service.create_node = AsyncMock(return_value=sample_node_data)

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.SKILL,
            name="web-scraper",
            description="Web scraping utility",
            tags=["web", "scraping"],
            properties={
                "skill_path": "/path/to/skill",
                "has_env_file": True,
            },
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Created" in result[0].text
        assert "skill-abc123" in result[0].text or "ID:" in result[0].text

    @pytest.mark.asyncio
    async def test_create_script_node(self, mock_graph_service):
        """Test creating a Script node."""
        script_data = {
            "id": "script-xyz789",
            "type": "Script",
            "name": "main.py",
            "description": "Main script",
            "tags": ["python"],
            "properties": {
                "language": "python",
                "file_path": "/path/to/main.py",
                "is_executable": True,
            },
        }
        mock_graph_service.create_node = AsyncMock(return_value=script_data)

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.SCRIPT,
            name="main.py",
            properties={"language": "python"},
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_create_knowledge_node(self, mock_graph_service):
        """Test creating a Knowledge node."""
        knowledge_data = {
            "id": "knowledge-def456",
            "type": "Knowledge",
            "name": "Tutorial",
            "properties": {"category": "tutorial"},
        }
        mock_graph_service.create_node = AsyncMock(return_value=knowledge_data)

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.KNOWLEDGE,
            name="Tutorial",
            properties={"category": "tutorial"},
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_create_tool_node(self, mock_graph_service):
        """Test creating a Tool node."""
        tool_data = {
            "id": "tool-mno123",
            "type": "Tool",
            "name": "web_fetch",
            "properties": {"mcp_server": "web-tools"},
        }
        mock_graph_service.create_node = AsyncMock(return_value=tool_data)

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.TOOL,
            name="web_fetch",
            properties={"mcp_server": "web-tools"},
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_create_with_custom_id(self, mock_graph_service):
        """Test creating a node with custom ID."""
        custom_data = {
            "id": "custom-id-123",
            "type": "Skill",
            "name": "custom-skill",
        }
        mock_graph_service.create_node = AsyncMock(return_value=custom_data)

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.SKILL,
            node_id="custom-id-123",
            name="custom-skill",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Created" in result[0].text

    @pytest.mark.asyncio
    async def test_create_missing_node_type(self, mock_graph_service):
        """Test that create fails without node_type."""
        input_data = NodeCrudInput(
            operation="create",
            name="test",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "node_type is required" in result[0].text

    @pytest.mark.asyncio
    async def test_create_missing_name(self, mock_graph_service):
        """Test that create fails without name."""
        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.SKILL,
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "name is required" in result[0].text

    @pytest.mark.asyncio
    async def test_create_error_handling(self, mock_graph_service):
        """Test create error handling."""
        mock_graph_service.create_node = AsyncMock(
            side_effect=GraphServiceError("Connection failed")
        )

        input_data = NodeCrudInput(
            operation="create",
            node_type=NodeType.SKILL,
            name="test-skill",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Error creating node" in result[0].text


class TestNodeCrudRead:
    """Tests for read operation."""

    @pytest.mark.asyncio
    async def test_read_existing_node(self, mock_graph_service, sample_node_data):
        """Test reading an existing node."""
        mock_graph_service.get_node = AsyncMock(return_value=sample_node_data)

        input_data = NodeCrudInput(
            operation="read",
            node_id="skill-abc123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "web-scraper" in result[0].text
        assert "Skill" in result[0].text

    @pytest.mark.asyncio
    async def test_read_nonexistent_node(self, mock_graph_service):
        """Test reading a node that doesn't exist."""
        mock_graph_service.get_node = AsyncMock(return_value=None)

        input_data = NodeCrudInput(
            operation="read",
            node_id="nonexistent-123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_read_missing_node_id(self, mock_graph_service):
        """Test that read fails without node_id."""
        input_data = NodeCrudInput(
            operation="read",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "node_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_read_error_handling(self, mock_graph_service):
        """Test read error handling."""
        mock_graph_service.get_node = AsyncMock(side_effect=GraphServiceError("Query failed"))

        input_data = NodeCrudInput(
            operation="read",
            node_id="skill-123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Error reading node" in result[0].text


class TestNodeCrudUpdate:
    """Tests for update operation."""

    @pytest.mark.asyncio
    async def test_update_node_description(self, mock_graph_service, sample_node_data):
        """Test updating node description."""
        updated_data = sample_node_data.copy()
        updated_data["description"] = "Updated description"
        mock_graph_service.update_node = AsyncMock(return_value=updated_data)

        input_data = NodeCrudInput(
            operation="update",
            node_id="skill-abc123",
            description="Updated description",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Updated node" in result[0].text

    @pytest.mark.asyncio
    async def test_update_node_tags(self, mock_graph_service, sample_node_data):
        """Test updating node tags."""
        updated_data = sample_node_data.copy()
        updated_data["tags"] = ["new", "tags"]
        mock_graph_service.update_node = AsyncMock(return_value=updated_data)

        input_data = NodeCrudInput(
            operation="update",
            node_id="skill-abc123",
            tags=["new", "tags"],
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Updated node" in result[0].text

    @pytest.mark.asyncio
    async def test_update_node_properties(self, mock_graph_service, sample_node_data):
        """Test updating node properties."""
        updated_data = sample_node_data.copy()
        updated_data["properties"]["new_prop"] = "new_value"
        mock_graph_service.update_node = AsyncMock(return_value=updated_data)

        input_data = NodeCrudInput(
            operation="update",
            node_id="skill-abc123",
            properties={"new_prop": "new_value"},
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Updated node" in result[0].text

    @pytest.mark.asyncio
    async def test_update_missing_node_id(self, mock_graph_service):
        """Test that update fails without node_id."""
        input_data = NodeCrudInput(
            operation="update",
            description="New description",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "node_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_update_no_changes(self, mock_graph_service):
        """Test that update fails without any update fields."""
        input_data = NodeCrudInput(
            operation="update",
            node_id="skill-123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "No properties" in result[0].text or "No update" in result[0].text

    @pytest.mark.asyncio
    async def test_update_error_handling(self, mock_graph_service):
        """Test update error handling."""
        mock_graph_service.update_node = AsyncMock(side_effect=GraphServiceError("Update failed"))

        input_data = NodeCrudInput(
            operation="update",
            node_id="skill-123",
            description="New description",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Error updating node" in result[0].text


class TestNodeCrudDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_existing_node(self, mock_graph_service):
        """Test deleting an existing node."""
        mock_graph_service.delete_node = AsyncMock()

        input_data = NodeCrudInput(
            operation="delete",
            node_id="skill-abc123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Deleted node" in result[0].text
        assert "skill-abc123" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_missing_node_id(self, mock_graph_service):
        """Test that delete fails without node_id."""
        input_data = NodeCrudInput(
            operation="delete",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "node_id is required" in result[0].text

    @pytest.mark.asyncio
    async def test_delete_error_handling(self, mock_graph_service):
        """Test delete error handling."""
        mock_graph_service.delete_node = AsyncMock(side_effect=GraphServiceError("Delete failed"))

        input_data = NodeCrudInput(
            operation="delete",
            node_id="skill-123",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Error deleting node" in result[0].text


class TestNodeCrudList:
    """Tests for list operation."""

    @pytest.mark.asyncio
    async def test_list_all_nodes(self, mock_graph_service):
        """Test listing all nodes."""
        nodes = [
            {"id": "skill-1", "type": "Skill", "name": "skill1", "description": ""},
            {"id": "skill-2", "type": "Skill", "name": "skill2", "description": ""},
        ]
        mock_graph_service.list_nodes = AsyncMock(return_value=nodes)

        input_data = NodeCrudInput(operation="list")

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "2 Nodes" in result[0].text
        assert "skill1" in result[0].text
        assert "skill2" in result[0].text

    @pytest.mark.asyncio
    async def test_list_by_node_type(self, mock_graph_service):
        """Test listing nodes filtered by type."""
        scripts = [
            {"id": "script-1", "type": "Script", "name": "main.py", "description": ""},
            {"id": "script-2", "type": "Script", "name": "utils.py", "description": ""},
        ]
        mock_graph_service.list_nodes = AsyncMock(return_value=scripts)

        input_data = NodeCrudInput(
            operation="list",
            node_type=NodeType.SCRIPT,
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "main.py" in result[0].text
        assert "utils.py" in result[0].text

    @pytest.mark.asyncio
    async def test_list_with_limit(self, mock_graph_service):
        """Test listing nodes with limit."""
        nodes = [
            {"id": f"node-{i}", "type": "Skill", "name": f"skill{i}", "description": ""}
            for i in range(10)
        ]
        mock_graph_service.list_nodes = AsyncMock(return_value=nodes)

        input_data = NodeCrudInput(
            operation="list",
            limit=5,
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        # Should show message about showing limited results
        assert "10 Nodes" in result[0].text

    @pytest.mark.asyncio
    async def test_list_empty_result(self, mock_graph_service):
        """Test listing when no nodes exist."""
        mock_graph_service.list_nodes = AsyncMock(return_value=[])

        input_data = NodeCrudInput(operation="list")

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "No nodes found" in result[0].text

    @pytest.mark.asyncio
    async def test_list_error_handling(self, mock_graph_service):
        """Test list error handling."""
        mock_graph_service.list_nodes = AsyncMock(side_effect=GraphServiceError("List failed"))

        input_data = NodeCrudInput(operation="list")

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "Error listing nodes" in result[0].text


class TestNodeCrudGeneral:
    """General tests for NodeCrud tool."""

    @pytest.mark.asyncio
    @patch("skill_mcp.tools.node_crud.GRAPH_ENABLED", False)
    async def test_graph_disabled(self):
        """Test that tool returns error when graph is disabled."""
        input_data = NodeCrudInput(
            operation="list",
        )

        result = await NodeCrud.node_crud(input_data)

        assert len(result) == 1
        assert "not enabled" in result[0].text.lower()

    def test_tool_definition(self):
        """Test that get_tool_definition returns valid tool."""
        tools = NodeCrud.get_tool_definition()

        assert len(tools) == 1
        assert tools[0].name == "node_crud"
        assert "CRUD" in tools[0].description
        assert tools[0].inputSchema is not None
