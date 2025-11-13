"""Graph database service for Neo4j knowledge graph operations."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from skill_mcp.core.config import (
    GRAPH_ENABLED,
    GRAPH_MAX_TRAVERSAL_DEPTH,
    GRAPH_QUERY_TIMEOUT,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    SKILLS_DIR,
)
from skill_mcp.core.exceptions import SkillNotFoundError
from skill_mcp.models import FileInfo, ScriptInfo, SkillDetails
from skill_mcp.services.script_service import extract_pep723_dependencies
from skill_mcp.services.skill_service import SkillService
from skill_mcp.utils.ast_analyzer import PythonImportAnalyzer
from skill_mcp.utils.graph_utils import get_current_timestamps, require_connection
from skill_mcp.utils.script_detector import get_file_type

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
    """Service for Neo4j graph database operations."""

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
            raise GraphServiceError(
                "neo4j package not installed. Install with: pip install neo4j"
            )

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
    # Helper Methods
    # ===================

    def _execute_single_result_query(
        self, query: str, params: Dict[str, Any], result_key: str
    ) -> Dict[str, Any]:
        """
        Execute query expecting single result node.

        Args:
            query: Cypher query string
            params: Query parameters
            result_key: Key to extract from result record

        Returns:
            Dictionary with node properties or empty dict
        """
        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params)
            record = result.single()
            if record:
                return dict(record[result_key])
            return {}

    def _execute_write_query(self, query: str, params: Dict[str, Any]) -> None:
        """
        Execute write query without expecting results.

        Args:
            query: Cypher query string
            params: Query parameters
        """
        with GraphService._driver.session(database=NEO4J_DATABASE) as session:
            session.run(query, params)

    # ===================
    # Node Operations
    # ===================

    @require_connection
    async def create_skill_node(self, skill_details: SkillDetails) -> Dict[str, Any]:
        """
        Create or update a skill node in the graph.

        Args:
            skill_details: SkillDetails object with complete skill info

        Returns:
            Dictionary with node properties
        """
        query = """
        MERGE (s:Skill {name: $name})
        SET s.description = $description,
            s.has_env_file = $has_env_file,
            s.file_count = $file_count,
            s.script_count = $script_count,
            s.updated_at = datetime($updated_at)
        ON CREATE SET s.created_at = datetime($created_at)
        RETURN s
        """

        timestamps = get_current_timestamps()
        params = {
            "name": skill_details.name,
            "description": skill_details.description,
            "has_env_file": skill_details.has_env_file,
            "file_count": len(skill_details.files),
            "script_count": len(skill_details.scripts),
            **timestamps,
        }

        return self._execute_single_result_query(query, params, "s")

    @require_connection
    async def create_file_node(
        self, skill_name: str, file_info: FileInfo
    ) -> Dict[str, Any]:
        """
        Create or update a file node.

        Args:
            skill_name: Name of the skill
            file_info: FileInfo object

        Returns:
            Dictionary with node properties
        """
        # Determine labels based on file type
        labels = self._get_file_labels(file_info)
        label_str = ":".join(labels)

        query = f"""
        MERGE (f:{label_str} {{path: $path, skill_name: $skill_name}})
        SET f.type = $type,
            f.size = $size,
            f.is_executable = $is_executable,
            f.modified_at = datetime($modified_at)
        RETURN f
        """

        params = {
            "path": file_info.path,
            "skill_name": skill_name,
            "type": file_info.type,
            "size": file_info.size,
            "is_executable": file_info.is_executable,
            "modified_at": (
                datetime.fromtimestamp(file_info.modified).isoformat()
                if file_info.modified
                else datetime.now().isoformat()
            ),
        }

        return self._execute_single_result_query(query, params, "f")

    def _get_file_labels(self, file_info: FileInfo) -> List[str]:
        """
        Determine Neo4j labels for a file based on its type.

        Args:
            file_info: FileInfo object

        Returns:
            List of labels to apply to the file node
        """
        labels = ["File"]

        if file_info.type == "python":
            labels.append("Python")
        elif file_info.type == "shell":
            labels.append("Shell")
        elif file_info.type == "markdown":
            labels.append("Markdown")

        if file_info.is_executable:
            labels.append("Script")

        return labels

    @require_connection
    async def create_dependency_node(
        self, package: str, version: str, ecosystem: str = "python"
    ) -> Dict[str, Any]:
        """
        Create or update a dependency node.

        Args:
            package: Package name (e.g., 'requests')
            version: Version specification (e.g., '>=2.31.0')
            ecosystem: Package ecosystem ('python', 'npm', etc.)

        Returns:
            Dictionary with node properties
        """
        query = """
        MERGE (d:Dependency {package_name: $package, ecosystem: $ecosystem})
        SET d.version_spec = $version,
            d.updated_at = datetime($updated_at)
        ON CREATE SET d.created_at = datetime($created_at)
        RETURN d
        """

        timestamps = get_current_timestamps()
        params = {
            "package": package,
            "version": version,
            "ecosystem": ecosystem,
            **timestamps,
        }

        return self._execute_single_result_query(query, params, "d")

    @require_connection
    async def create_env_var_node(self, skill_name: str, key: str) -> Dict[str, Any]:
        """
        Create environment variable node (key only, no value for security).

        Args:
            skill_name: Name of the skill
            key: Environment variable key

        Returns:
            Dictionary with node properties
        """
        query = """
        MERGE (e:EnvVar {key: $key, skill_name: $skill_name})
        SET e.updated_at = datetime($updated_at)
        ON CREATE SET e.created_at = datetime($created_at)
        RETURN e
        """

        timestamps = get_current_timestamps()
        params = {
            "key": key,
            "skill_name": skill_name,
            **timestamps,
        }

        return self._execute_single_result_query(query, params, "e")

    @require_connection
    async def create_knowledge_node(
        self,
        knowledge_id: str,
        title: str,
        content: str,
        category: str = "note",
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create or update a knowledge document node.

        Args:
            knowledge_id: Unique identifier (e.g., filename without extension)
            title: Title of the knowledge document
            content: Content (markdown text)
            category: Category (tutorial, guide, reference, note, article)
            tags: List of tags for categorization
            author: Optional author name

        Returns:
            Dictionary with node properties
        """
        query = """
        MERGE (k:Knowledge {id: $knowledge_id})
        SET k.title = $title,
            k.content = $content,
            k.category = $category,
            k.tags = $tags,
            k.author = $author,
            k.updated_at = datetime($updated_at)
        ON CREATE SET k.created_at = datetime($created_at)
        RETURN k
        """

        timestamps = get_current_timestamps()
        params = {
            "knowledge_id": knowledge_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "author": author,
            **timestamps,
        }

        return self._execute_single_result_query(query, params, "k")

    @require_connection
    async def delete_knowledge_node(self, knowledge_id: str) -> None:
        """Delete a knowledge node and its relationships."""
        query = """
        MATCH (k:Knowledge {id: $knowledge_id})
        DETACH DELETE k
        """

        params = {"knowledge_id": knowledge_id}
        self._execute_write_query(query, params)

    # ===================
    # Relationship Operations
    # ===================

    @require_connection
    async def link_skill_to_file(self, skill_name: str, file_path: str) -> None:
        """Create [:HAS_FILE] relationship between skill and file."""
        query = """
        MATCH (s:Skill {name: $skill_name})
        MATCH (f:File {path: $file_path, skill_name: $skill_name})
        MERGE (s)-[:HAS_FILE]->(f)
        """
        params = {"skill_name": skill_name, "file_path": file_path}
        self._execute_write_query(query, params)

    @require_connection
    async def link_file_to_dependency(
        self, skill_name: str, file_path: str, package: str, ecosystem: str = "python"
    ) -> None:
        """Create [:DEPENDS_ON] relationship between file and dependency."""
        query = """
        MATCH (f:File {path: $file_path, skill_name: $skill_name})
        MATCH (d:Dependency {package_name: $package, ecosystem: $ecosystem})
        MERGE (f)-[:DEPENDS_ON]->(d)
        """
        params = {
            "skill_name": skill_name,
            "file_path": file_path,
            "package": package,
            "ecosystem": ecosystem,
        }
        self._execute_write_query(query, params)

    @require_connection
    async def link_file_imports(
        self, skill_name: str, from_file: str, to_module: str, import_type: str = "local"
    ) -> None:
        """Create [:IMPORTS] relationship between files."""
        query = """
        MATCH (f1:File {path: $from_file, skill_name: $skill_name})
        MERGE (m:Module {name: $to_module, type: $import_type})
        MERGE (f1)-[:IMPORTS {type: $import_type}]->(m)
        """
        params = {
            "skill_name": skill_name,
            "from_file": from_file,
            "to_module": to_module,
            "import_type": import_type,
        }
        self._execute_write_query(query, params)

    @require_connection
    async def link_cross_skill_reference(
        self, from_skill: str, to_skill: str, via_file: str
    ) -> None:
        """Create [:REFERENCES] relationship for cross-skill imports."""
        query = """
        MATCH (s1:Skill {name: $from_skill})
        MATCH (s2:Skill {name: $to_skill})
        MERGE (s1)-[r:REFERENCES {via_file: $via_file}]->(s2)
        SET r.updated_at = datetime($updated_at)
        """
        timestamps = get_current_timestamps()
        params = {
            "from_skill": from_skill,
            "to_skill": to_skill,
            "via_file": via_file,
            "updated_at": timestamps["updated_at"],
        }
        self._execute_write_query(query, params)

    @require_connection
    async def link_skill_to_env_var(self, skill_name: str, key: str) -> None:
        """Create [:HAS_ENV_VAR] relationship."""
        query = """
        MATCH (s:Skill {name: $skill_name})
        MATCH (e:EnvVar {key: $key, skill_name: $skill_name})
        MERGE (s)-[:HAS_ENV_VAR]->(e)
        """
        params = {"skill_name": skill_name, "key": key}
        self._execute_write_query(query, params)

    @require_connection
    async def link_knowledge_to_skill(
        self, knowledge_id: str, skill_name: str, relationship_type: str = "EXPLAINS"
    ) -> None:
        """
        Create relationship between knowledge and skill.

        Args:
            knowledge_id: ID of the knowledge document
            skill_name: Name of the skill
            relationship_type: Type of relationship (EXPLAINS, REFERENCES, USES)
        """
        # Validate relationship type
        valid_types = {"EXPLAINS", "REFERENCES", "USES"}
        if relationship_type not in valid_types:
            raise GraphServiceError(
                f"Invalid relationship type: {relationship_type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        query = f"""
        MATCH (k:Knowledge {{id: $knowledge_id}})
        MATCH (s:Skill {{name: $skill_name}})
        MERGE (k)-[:{relationship_type}]->(s)
        """
        params = {"knowledge_id": knowledge_id, "skill_name": skill_name}
        self._execute_write_query(query, params)

    @require_connection
    async def link_knowledge_to_knowledge(
        self, from_knowledge_id: str, to_knowledge_id: str
    ) -> None:
        """Create [:RELATED_TO] relationship between knowledge documents."""
        query = """
        MATCH (k1:Knowledge {id: $from_id})
        MATCH (k2:Knowledge {id: $to_id})
        MERGE (k1)-[:RELATED_TO]->(k2)
        """
        params = {"from_id": from_knowledge_id, "to_id": to_knowledge_id}
        self._execute_write_query(query, params)

    # ===================
    # Sync Operations
    # ===================

    @require_connection
    async def sync_skill_to_graph(self, skill_name: str) -> Dict[str, Any]:
        """
        Sync entire skill structure to graph.

        Args:
            skill_name: Name of the skill to sync

        Returns:
            Dictionary with sync statistics
        """

        try:
            # Get skill details
            skill_details = SkillService.get_skill_details(skill_name)

            # Create skill node
            await self.create_skill_node(skill_details)

            # Track statistics
            stats = {
                "skill": skill_name,
                "files_synced": 0,
                "dependencies_found": 0,
                "imports_found": 0,
                "env_vars_synced": 0,
            }

            # Create file nodes and analyze
            for file_info in skill_details.files:
                await self.create_file_node(skill_name, file_info)
                await self.link_skill_to_file(skill_name, file_info.path)
                stats["files_synced"] += 1

                # Analyze Python files for imports and dependencies
                if file_info.type == "python":
                    file_path = SKILLS_DIR / skill_name / file_info.path
                    await self._analyze_python_file(skill_name, file_path, file_info.path, stats)

            # Sync environment variables
            for env_key in skill_details.env_vars:
                await self.create_env_var_node(skill_name, env_key)
                await self.link_skill_to_env_var(skill_name, env_key)
                stats["env_vars_synced"] += 1

            return stats

        except SkillNotFoundError as e:
            raise GraphServiceError(f"Skill not found: {str(e)}")
        except Exception as e:
            raise GraphServiceError(f"Failed to sync skill to graph: {str(e)}")

    async def _analyze_python_file(
        self, skill_name: str, file_path: Path, relative_path: str, stats: Dict[str, Any]
    ) -> None:
        """Analyze a Python file for imports and dependencies."""
        # Extract imports
        imports = PythonImportAnalyzer.extract_imports(file_path)

        # Create import relationships
        for import_type in ["standard_lib", "third_party", "local"]:
            for module in imports[import_type]:
                await self.link_file_imports(skill_name, relative_path, module, import_type)
                stats["imports_found"] += 1

        # Extract PEP 723 dependencies
        try:
            content = file_path.read_text(encoding="utf-8")
            deps = extract_pep723_dependencies(content)
            for dep in deps:
                # Parse package name from version spec
                package_name = dep.split(">=")[0].split("==")[0].split("<")[0].strip()
                await self.create_dependency_node(package_name, dep, "python")
                await self.link_file_to_dependency(
                    skill_name, relative_path, package_name, "python"
                )
                stats["dependencies_found"] += 1
        except Exception:
            pass

    @require_connection
    async def sync_all_skills_to_graph(self) -> Dict[str, Any]:
        """
        Sync all skills to the graph database.

        Returns:
            Dictionary with overall sync statistics
        """

        skills = SkillService.list_skills()
        overall_stats = {
            "total_skills": len(skills),
            "skills_synced": 0,
            "total_files": 0,
            "total_dependencies": 0,
            "total_imports": 0,
            "errors": [],
        }

        for skill_summary in skills:
            try:
                stats = await self.sync_skill_to_graph(skill_summary.name)
                overall_stats["skills_synced"] += 1
                overall_stats["total_files"] += stats["files_synced"]
                overall_stats["total_dependencies"] += stats["dependencies_found"]
                overall_stats["total_imports"] += stats["imports_found"]
            except Exception as e:
                overall_stats["errors"].append(f"{skill_summary.name}: {str(e)}")

        return overall_stats

    @require_connection
    async def delete_skill_from_graph(self, skill_name: str) -> None:
        """Delete a skill and its relationships from the graph."""
        query = """
        MATCH (s:Skill {name: $skill_name})
        OPTIONAL MATCH (s)-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (s)-[:HAS_ENV_VAR]->(e:EnvVar)
        DETACH DELETE s, f, e
        """
        params = {"skill_name": skill_name}
        self._execute_write_query(query, params)

    # ===================
    # Query Operations
    # ===================

    @require_connection
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw Cypher query.

        Args:
            query: Cypher query string
            params: Query parameters

        Returns:
            List of result records as dictionaries
        """
        params = params or {}

        try:
            with GraphService._driver.session(database=NEO4J_DATABASE) as session:
                result = session.run(query, params, timeout=GRAPH_QUERY_TIMEOUT)
                return [dict(record) for record in result]
        except Exception as e:
            raise GraphServiceError(f"Query execution failed: {str(e)}")

    @require_connection
    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph."""

        query = """
        MATCH (n)
        RETURN labels(n)[0] as node_type, count(*) as count
        ORDER BY count DESC
        """

        results = await self.execute_query(query)

        stats = {"node_counts": {}, "total_nodes": 0}
        for record in results:
            node_type = record.get("node_type", "Unknown")
            count = record.get("count", 0)
            stats["node_counts"][node_type] = count
            stats["total_nodes"] += count

        # Get relationship counts
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY count DESC
        """

        rel_results = await self.execute_query(rel_query)
        stats["relationship_counts"] = {}
        stats["total_relationships"] = 0

        for record in rel_results:
            rel_type = record.get("rel_type", "Unknown")
            count = record.get("count", 0)
            stats["relationship_counts"][rel_type] = count
            stats["total_relationships"] += count

        return stats

    async def record_script_execution(
        self, skill_name: str, script_path: str, success: bool, timestamp: Optional[datetime] = None
    ) -> None:
        """Record a script execution for tracking purposes."""
        if not self.is_connected():
            return  # Silently skip if not connected

        if timestamp is None:
            timestamp = datetime.now()

        query = """
        MATCH (s:Skill {name: $skill_name})
        MATCH (f:File {path: $script_path, skill_name: $skill_name})
        MERGE (s)-[r:EXECUTED {script_path: $script_path}]->(f)
        SET r.last_executed = datetime($timestamp),
            r.last_success = $success,
            r.execution_count = coalesce(r.execution_count, 0) + 1
        """

        params = {
            "skill_name": skill_name,
            "script_path": script_path,
            "timestamp": timestamp.isoformat(),
            "success": success,
        }

        try:
            with GraphService._driver.session(database=NEO4J_DATABASE) as session:
                session.run(query, params)
        except Exception:
            # Silently fail - don't break script execution
            pass
