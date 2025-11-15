"""Utility functions and decorators for graph operations."""

import functools
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from skill_mcp.core.config import GRAPH_AUTO_SYNC, GRAPH_ENABLED


def require_connection(func: Callable) -> Callable:
    """
    Decorator to ensure graph connection before executing method.

    Raises:
        GraphServiceError: If not connected to Neo4j
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            from skill_mcp.services.graph_service import GraphServiceError
            raise GraphServiceError("Not connected to Neo4j")
        return await func(self, *args, **kwargs)
    return wrapper


def get_current_timestamps() -> Dict[str, str]:
    """
    Get current timestamp for created_at and updated_at fields.

    Returns:
        Dictionary with 'created_at' and 'updated_at' as ISO format strings
    """
    now = datetime.now().isoformat()
    return {"created_at": now, "updated_at": now}


async def auto_sync_skill_to_graph(skill_name: str) -> None:
    """
    Auto-sync skill to graph if feature is enabled.

    This is a helper that silently fails if graph is not enabled or sync fails.
    Use this in CRUD operations to keep graph in sync automatically.

    Args:
        skill_name: Name of the skill to sync
    """
    if not GRAPH_ENABLED or not GRAPH_AUTO_SYNC:
        return

    try:
        from skill_mcp.services.graph_service import GraphService

        graph_service = GraphService()
        await graph_service.sync_skill_to_graph(skill_name)
    except Exception:
        # Silently fail - don't break CRUD operations if graph sync fails
        pass


async def auto_delete_skill_from_graph(skill_name: str) -> None:
    """
    Auto-delete skill from graph if feature is enabled.

    Args:
        skill_name: Name of the skill to delete
    """
    if not GRAPH_ENABLED or not GRAPH_AUTO_SYNC:
        return

    try:
        from skill_mcp.services.graph_service import GraphService

        graph_service = GraphService()
        await graph_service.delete_skill_from_graph(skill_name)
    except Exception:
        # Silently fail - don't break delete operations
        pass
