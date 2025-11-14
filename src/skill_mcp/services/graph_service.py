"""Graph database service for Neo4j knowledge graph operations - Clean node-based architecture."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from skill_mcp.core.config import (
    GRAPH_ENABLED,
    GRAPH_MAX_TRAVERSAL_DEPTH,
    GRAPH_QUERY_TIMEOUT,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
)
from skill_mcp.models import Node, NodeType, Relationship, RelationshipType
from skill_mcp.utils.graph_utils import get_current_timestamps, require_connection

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable
except ImportError:
    GraphDatabase = None  # type: ignore
    ServiceUnavailable = Exception  # type: ignore


class GraphServiceError(Exception):
    """Base exception for graph service errors."""

    pass


class GraphService:
    """Service for Neo4j graph database operations with generic node/relationship operations."""

    _instance: Optional["GraphService"] = None
    _driver: Optional[Any] = None

    def __new__(cls) -> "GraphService":
        """Singleton pattern to reuse connection."""
        if cls._instance is None:
            cls._instance = super(GraphService, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize graph service."""
        if not GRAPH_ENABLED:
            return

        if GraphDatabase is None:
            raise GraphServiceError("neo4j package not installed. Install with: pip install neo4j")

        if GraphService._driver is None:
            self._connect()

    def _connect(self) -> None:
        """Connect to Neo4j database."""
        try:
            GraphService._driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            # Verify connection
            with GraphService._driver.session(database=NEO4J_DATABASE) as session:
                session.run("RETURN 1")
        except ServiceUnavailable as e:
            raise GraphServiceError(f"Cannot connect to Neo4j at {NEO4J_URI}: {str(e)}")
        except Exception as e:
            raise GraphServiceError(f"Failed to initialize Neo4j connection: {str(e)}")

    def close(self) -> None:
        """Close Neo4j connection."""
        if GraphService._driver:
            GraphService._driver.close()
            GraphService._driver = None

    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        if not GRAPH_ENABLED or not GraphService._driver:
            return False

        try:
            with GraphService._driver.session(database=NEO4J_DATABASE) as session:
                result = session.run("RETURN 1")
                result.single()
                return True
        except Exception:
            return False

    # ===================
    # Generic Node Operations
    # ===================

    @require_connection
    async def create_node(self, node: Node) -> Dict[str, Any]:
        """
        Create a new node in the graph.

        Args:
            node: Node object with all properties

        Returns:
            Dictionary with created node properties
        """
        timestamps = get_current_timestamps()

        # Handle both enum and string types
        node_type = node.type.value if hasattr(node.type, "value") else node.type

        query = f"""
        CREATE (n:{node_type} {{
            id: $id,
            name: $name,
            description: $description,
            tags: $tags,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        }})
        SET n += $properties
        RETURN n
        """

        params = {
            "id": node.id,
            "name": node.name,
            "description": node.description or "",
            "tags": node.tags,
            "properties": node.properties,
            **timestamps,
        }

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                return dict(record["n"])
            return {}

    @require_connection
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.

        Args:
            node_id: Unique node identifier

        Returns:
            Node properties dictionary or None if not found
        """
        query = """
        MATCH (n {id: $node_id})
        RETURN n, labels(n) as labels
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, {"node_id": node_id})
            record = result.single()
            if record:
                node_dict = dict(record["n"])
                node_dict["type"] = record["labels"][0] if record["labels"] else "Unknown"
                return node_dict
            return None

    @require_connection
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update node properties.

        Args:
            node_id: Unique node identifier
            properties: Properties to update

        Returns:
            Updated node properties
        """
        timestamps = get_current_timestamps()

        query = """
        MATCH (n {id: $node_id})
        SET n += $properties,
            n.updated_at = datetime($updated_at)
        RETURN n
        """

        params = {
            "node_id": node_id,
            "properties": properties,
            "updated_at": timestamps["updated_at"],
        }

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                return dict(record["n"])
            return {}

    @require_connection
    async def delete_node(self, node_id: str) -> None:
        """
        Delete a node and all its relationships.

        Args:
            node_id: Unique node identifier
        """
        query = """
        MATCH (n {id: $node_id})
        DETACH DELETE n
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            session.run(query, {"node_id": node_id})

    @require_connection
    async def list_nodes(
        self,
        node_type: Optional[NodeType] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List nodes with optional filtering.

        Args:
            node_type: Filter by node type
            filters: Additional filter criteria
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of node dictionaries
        """
        if node_type:
            match_clause = f"MATCH (n:{node_type.value})"
        else:
            match_clause = "MATCH (n)"

        where_clauses = []
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if filters:
            for key, value in filters.items():
                where_clauses.append(f"n.{key} = ${key}")
                params[key] = value

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
        {match_clause}
        {where_clause}
        RETURN n, labels(n) as labels
        ORDER BY n.updated_at DESC
        SKIP $offset
        LIMIT $limit
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params)
            nodes = []
            for record in result:
                node_dict = dict(record["n"])
                node_dict["type"] = record["labels"][0] if record["labels"] else "Unknown"
                nodes.append(node_dict)
            return nodes

    # ===================
    # Generic Relationship Operations
    # ===================

    @require_connection
    async def create_relationship(self, relationship: Relationship) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.

        Args:
            relationship: Relationship object

        Returns:
            Dictionary with relationship properties
        """
        timestamps = get_current_timestamps()

        # Handle both enum and string types
        rel_type = (
            relationship.type.value if hasattr(relationship.type, "value") else relationship.type
        )

        query = f"""
        MATCH (from {{id: $from_id}}), (to {{id: $to_id}})
        CREATE (from)-[r:{rel_type}]->(to)
        SET r += $properties,
            r.created_at = datetime($created_at)
        RETURN r
        """

        params = {
            "from_id": relationship.from_id,
            "to_id": relationship.to_id,
            "properties": relationship.properties,
            "created_at": timestamps["created_at"],
        }

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                return dict(record["r"])
            return {}

    @require_connection
    async def get_relationships(
        self,
        node_id: str,
        direction: str = "both",
        relationship_type: Optional[RelationshipType] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a node.

        Args:
            node_id: Node ID to get relationships for
            direction: "incoming", "outgoing", or "both"
            relationship_type: Optional filter by relationship type

        Returns:
            List of relationship dictionaries with connected nodes
        """
        type_filter = f":{relationship_type.value}" if relationship_type else ""

        if direction == "incoming":
            pattern = f"(other)-[r{type_filter}]->(n)"
        elif direction == "outgoing":
            pattern = f"(n)-[r{type_filter}]->(other)"
        else:  # both
            pattern = f"(n)-[r{type_filter}]-(other)"

        query = f"""
        MATCH {pattern}
        WHERE n.id = $node_id
        RETURN r, type(r) as rel_type,
               other.id as other_id,
               other.name as other_name,
               labels(other) as other_labels
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, {"node_id": node_id})
            relationships = []
            for record in result:
                rel_dict = {
                    "type": record["rel_type"],
                    "properties": dict(record["r"]),
                    "other_node": {
                        "id": record["other_id"],
                        "name": record["other_name"],
                        "type": record["other_labels"][0] if record["other_labels"] else "Unknown",
                    },
                }
                relationships.append(rel_dict)
            return relationships

    @require_connection
    async def delete_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: RelationshipType,
    ) -> None:
        """
        Delete a specific relationship.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship_type: Type of relationship to delete
        """
        query = f"""
        MATCH (from {{id: $from_id}})-[r:{relationship_type.value}]->(to {{id: $to_id}})
        DELETE r
        """

        params = {"from_id": from_id, "to_id": to_id}

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            session.run(query, params)

    @require_connection
    async def list_relationships(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List all relationships with optional filtering.

        Args:
            filters: Filter criteria
            limit: Maximum number of results

        Returns:
            List of relationship dictionaries
        """
        query = """
        MATCH (from)-[r]->(to)
        RETURN from.id as from_id, from.name as from_name, labels(from) as from_labels,
               to.id as to_id, to.name as to_name, labels(to) as to_labels,
               type(r) as rel_type, properties(r) as rel_properties
        LIMIT $limit
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, {"limit": limit})
            relationships = []
            for record in result:
                rel_dict = {
                    "from_node": {
                        "id": record["from_id"],
                        "name": record["from_name"],
                        "type": record["from_labels"][0] if record["from_labels"] else "Unknown",
                    },
                    "to_node": {
                        "id": record["to_id"],
                        "name": record["to_name"],
                        "type": record["to_labels"][0] if record["to_labels"] else "Unknown",
                    },
                    "type": record["rel_type"],
                    "properties": record["rel_properties"],
                }
                relationships.append(rel_dict)
            return relationships

    # ===================
    # Query Operations
    # ===================

    @require_connection
    async def query_cypher(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result dictionaries
        """
        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params or {}, timeout=GRAPH_QUERY_TIMEOUT)
            return result.data()

    @require_connection
    async def traverse_graph(
        self,
        start_node_id: str,
        direction: str = "both",
        max_depth: int = 3,
        relationship_types: Optional[List[RelationshipType]] = None,
        node_types: Optional[List[NodeType]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Traverse graph from starting node.

        Args:
            start_node_id: Starting node ID
            direction: "incoming", "outgoing", or "both"
            max_depth: Maximum traversal depth
            relationship_types: Filter by relationship types
            node_types: Filter by node types
            limit: Maximum number of nodes

        Returns:
            Dictionary with nodes and relationships
        """
        # Build relationship pattern
        rel_type_filter = ""
        if relationship_types:
            types = "|".join([rt.value for rt in relationship_types])
            rel_type_filter = f":{types}"

        if direction == "incoming":
            pattern = f"<-[r{rel_type_filter}*1..{max_depth}]-"
        elif direction == "outgoing":
            pattern = f"-[r{rel_type_filter}*1..{max_depth}]->"
        else:  # both
            pattern = f"-[r{rel_type_filter}*1..{max_depth}]-"

        # Build node filter
        node_filter = ""
        if node_types:
            type_conditions = " OR ".join([f"'{nt.value}' IN labels(other)" for nt in node_types])
            node_filter = f"WHERE {type_conditions}"

        query = f"""
        MATCH (start {{id: $start_id}})
        MATCH path = (start){pattern}(other)
        {node_filter}
        WITH nodes(path) as path_nodes, relationships(path) as path_rels
        UNWIND path_nodes as node
        WITH collect(DISTINCT {{
            id: node.id,
            name: node.name,
            type: labels(node)[0],
            properties: properties(node)
        }}) as nodes,
        path_rels
        UNWIND path_rels as rel
        WITH nodes, collect(DISTINCT {{
            from: startNode(rel).id,
            to: endNode(rel).id,
            type: type(rel),
            properties: properties(rel)
        }}) as relationships
        RETURN nodes[0..$limit] as nodes, relationships
        """

        params = {"start_id": start_node_id, "limit": limit}

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params, timeout=GRAPH_QUERY_TIMEOUT)
            record = result.single()
            if record:
                return {
                    "nodes": record["nodes"] or [],
                    "relationships": record["relationships"] or [],
                }
            return {"nodes": [], "relationships": []}

    @require_connection
    async def find_path(
        self,
        from_id: str,
        to_id: str,
        max_path_length: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find paths between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            max_path_length: Maximum path length

        Returns:
            List of paths (each path is a list of nodes)
        """
        query = f"""
        MATCH path = shortestPath((from {{id: $from_id}})-[*1..{max_path_length}]-(to {{id: $to_id}}))
        RETURN [node in nodes(path) | {{
            id: node.id,
            name: node.name,
            type: labels(node)[0]
        }}] as path_nodes,
        [rel in relationships(path) | {{
            type: type(rel)
        }}] as path_relationships
        LIMIT 10
        """

        params = {"from_id": from_id, "to_id": to_id}

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params, timeout=GRAPH_QUERY_TIMEOUT)
            paths = []
            for record in result:
                paths.append(
                    {
                        "nodes": record["path_nodes"],
                        "relationships": record["path_relationships"],
                    }
                )
            return paths

    @require_connection
    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Dictionary with node counts, relationship counts, etc.
        """
        query = """
        MATCH (n)
        WITH labels(n)[0] as node_type, count(n) as node_count
        WITH collect({type: node_type, count: node_count}) as node_counts
        MATCH ()-[r]->()
        WITH node_counts, type(r) as rel_type, count(r) as rel_count
        WITH node_counts, collect({type: rel_type, count: rel_count}) as rel_counts
        RETURN node_counts, rel_counts,
               reduce(total = 0, nc IN node_counts | total + nc.count) as total_nodes,
               reduce(total = 0, rc IN rel_counts | total + rc.count) as total_relationships
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query)
            record = result.single()
            if record:
                node_counts = {nc["type"]: nc["count"] for nc in record["node_counts"]}
                rel_counts = {rc["type"]: rc["count"] for rc in record["rel_counts"]}
                return {
                    "node_counts": node_counts,
                    "relationship_counts": rel_counts,
                    "total_nodes": record["total_nodes"],
                    "total_relationships": record["total_relationships"],
                }
            return {
                "node_counts": {},
                "relationship_counts": {},
                "total_nodes": 0,
                "total_relationships": 0,
            }

    # ===================
    # EnvFile Helper Methods
    # ===================

    @require_connection
    async def get_env_files_for_node(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get all EnvFile nodes linked to a specific node (Script or Skill).

        Args:
            node_id: ID of the node to get env files for

        Returns:
            List of EnvFile node dictionaries with file_path properties
        """
        query = """
        MATCH (node {id: $node_id})-[:USES_ENV]->(env:EnvFile)
        RETURN env
        """

        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, {"node_id": node_id})
            records = result.data()

            env_files = []
            for record in records:
                env_node = record.get("env")
                if env_node:
                    env_files.append(dict(env_node))

            return env_files

    # ===================
    # Backward Compatibility (will be removed)
    # ===================

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Backward compatibility wrapper for query_cypher."""
        return await self.query_cypher(query, params)
