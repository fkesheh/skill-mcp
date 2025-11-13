"""Predefined Cypher queries for common graph operations."""

from typing import Dict


class GraphQueries:
    """Collection of predefined Cypher queries for skill graph operations."""

    @staticmethod
    def find_related_skills(skill_name: str, depth: int = 2) -> Dict[str, str]:
        """
        Find skills related through imports, dependencies, or references.

        Args:
            skill_name: Name of the skill to find relations for
            depth: Maximum traversal depth (1-5)

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH path = (s:Skill {name: $skill_name})-[*1..$depth]-(related:Skill)
        WHERE s <> related
        WITH related, path,
             length(path) as distance,
             [r in relationships(path) | type(r)] as relationship_types
        RETURN DISTINCT related.name as skill,
               related.description as description,
               distance,
               relationship_types
        ORDER BY distance, related.name
        """
        return {"query": query, "params": {"skill_name": skill_name, "depth": depth}}

    @staticmethod
    def get_dependency_tree(skill_name: str) -> Dict[str, str]:
        """
        Get complete dependency tree for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (f)-[:DEPENDS_ON]->(d:Dependency)
        WITH s, f, collect(DISTINCT {
            package: d.package_name,
            version: d.version_spec,
            ecosystem: d.ecosystem
        }) as dependencies
        RETURN s.name as skill,
               f.path as file,
               f.type as file_type,
               dependencies
        ORDER BY f.path
        """
        return {"query": query, "params": {"skill_name": skill_name}}

    @staticmethod
    def find_skills_using_dependency(package_name: str) -> Dict[str, str]:
        """
        Find all skills using a specific dependency.

        Args:
            package_name: Name of the package

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (d:Dependency {package_name: $package_name})<-[:DEPENDS_ON]-(f:File)-[:HAS_FILE]-(s:Skill)
        RETURN DISTINCT s.name as skill,
               s.description as description,
               collect(DISTINCT f.path) as files_using_package,
               d.version_spec as version_spec
        ORDER BY s.name
        """
        return {"query": query, "params": {"package_name": package_name}}

    @staticmethod
    def find_circular_dependencies() -> Dict[str, str]:
        """
        Detect circular dependencies between skills.

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH path = (s:Skill)-[:REFERENCES*2..]->(s)
        WITH [n in nodes(path) | n.name] as cycle
        RETURN DISTINCT cycle
        ORDER BY size(cycle)
        """
        return {"query": query, "params": {}}

    @staticmethod
    def get_most_used_dependencies(limit: int = 20) -> Dict[str, str]:
        """
        Get most commonly used dependencies across all skills.

        Args:
            limit: Maximum number of results

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (d:Dependency)<-[:DEPENDS_ON]-(f:File)
        WITH d, count(DISTINCT f) as file_count,
             collect(DISTINCT f.skill_name) as skills
        RETURN d.package_name as package,
               d.ecosystem as ecosystem,
               d.version_spec as version,
               file_count,
               size(skills) as skill_count,
               skills
        ORDER BY skill_count DESC, file_count DESC
        LIMIT $limit
        """
        return {"query": query, "params": {"limit": limit}}

    @staticmethod
    def find_orphaned_skills() -> Dict[str, str]:
        """
        Find skills with no relationships to other skills.

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill)
        WHERE NOT (s)-[:REFERENCES]-() AND NOT ()-[:REFERENCES]->(s)
        RETURN s.name as skill,
               s.description as description,
               s.file_count as file_count
        ORDER BY s.name
        """
        return {"query": query, "params": {}}

    @staticmethod
    def get_skill_complexity_score(skill_name: str) -> Dict[str, str]:
        """
        Calculate complexity score based on files, dependencies, relationships.

        Args:
            skill_name: Name of the skill

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})
        OPTIONAL MATCH (s)-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (f)-[:DEPENDS_ON]->(d:Dependency)
        OPTIONAL MATCH (s)-[:REFERENCES]->(other:Skill)
        OPTIONAL MATCH (s)<-[:REFERENCES]-(referrer:Skill)
        WITH s,
             count(DISTINCT f) as file_count,
             count(DISTINCT d) as dependency_count,
             count(DISTINCT other) as references_out,
             count(DISTINCT referrer) as references_in
        RETURN s.name as skill,
               s.description as description,
               file_count,
               dependency_count,
               references_out,
               references_in,
               (file_count + dependency_count * 2 + references_out * 3 + references_in) as complexity_score
        """
        return {"query": query, "params": {"skill_name": skill_name}}

    @staticmethod
    def get_import_graph(skill_name: str) -> Dict[str, str]:
        """
        Get import relationships for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (f)-[i:IMPORTS]->(m:Module)
        RETURN f.path as file,
               collect({module: m.name, type: i.type}) as imports
        ORDER BY f.path
        """
        return {"query": query, "params": {"skill_name": skill_name}}

    @staticmethod
    def find_skills_by_description(search_term: str) -> Dict[str, str]:
        """
        Search skills by description (case-insensitive).

        Args:
            search_term: Text to search for

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill)
        WHERE toLower(s.description) CONTAINS toLower($search_term)
           OR toLower(s.name) CONTAINS toLower($search_term)
        RETURN s.name as skill,
               s.description as description,
               s.file_count as file_count,
               s.script_count as script_count
        ORDER BY s.name
        """
        return {"query": query, "params": {"search_term": search_term}}

    @staticmethod
    def get_skill_impact_analysis(skill_name: str) -> Dict[str, str]:
        """
        Analyze what would break if this skill is modified/deleted.

        Args:
            skill_name: Name of the skill

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})

        // Find skills that reference this skill
        OPTIONAL MATCH (referrer:Skill)-[ref:REFERENCES]->(s)
        WITH s, collect(DISTINCT {
            skill: referrer.name,
            via_file: ref.via_file
        }) as referrers

        // Find files in this skill that others might depend on
        OPTIONAL MATCH (s)-[:HAS_FILE]->(f:File)
        WITH s, referrers, collect(DISTINCT f.path) as files

        // Find dependencies this skill provides
        OPTIONAL MATCH (s)-[:HAS_FILE]->(f2:File)-[:DEPENDS_ON]->(d:Dependency)
        WITH s, referrers, files, collect(DISTINCT d.package_name) as dependencies

        RETURN s.name as skill,
               referrers,
               files,
               dependencies,
               size(referrers) as impact_score
        """
        return {"query": query, "params": {"skill_name": skill_name}}

    @staticmethod
    def get_execution_history(skill_name: str, limit: int = 10) -> Dict[str, str]:
        """
        Get recent script execution history for a skill.

        Args:
            skill_name: Name of the skill
            limit: Maximum number of executions to return

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})-[e:EXECUTED]->(f:File)
        RETURN f.path as script,
               e.last_executed as last_executed,
               e.last_success as last_success,
               e.execution_count as execution_count
        ORDER BY e.last_executed DESC
        LIMIT $limit
        """
        return {"query": query, "params": {"skill_name": skill_name, "limit": limit}}

    @staticmethod
    def find_similar_skills(skill_name: str, limit: int = 5) -> Dict[str, str]:
        """
        Find skills with similar dependencies or structure.

        Args:
            skill_name: Name of the skill
            limit: Maximum number of results

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (s:Skill {name: $skill_name})-[:HAS_FILE]->(:File)-[:DEPENDS_ON]->(d:Dependency)
        WITH s, collect(DISTINCT d.package_name) as deps

        MATCH (other:Skill)-[:HAS_FILE]->(:File)-[:DEPENDS_ON]->(d2:Dependency)
        WHERE other <> s
        WITH s, deps, other, collect(DISTINCT d2.package_name) as other_deps

        // Calculate Jaccard similarity
        WITH s, other,
             [dep IN deps WHERE dep IN other_deps] as common,
             deps, other_deps
        WITH s, other,
             size(common) as common_count,
             size(deps) + size(other_deps) - size(common) as total_unique
        WHERE common_count > 0

        RETURN other.name as skill,
               other.description as description,
               common_count,
               total_unique,
               toFloat(common_count) / toFloat(total_unique) as similarity_score
        ORDER BY similarity_score DESC, common_count DESC
        LIMIT $limit
        """
        return {"query": query, "params": {"skill_name": skill_name, "limit": limit}}

    @staticmethod
    def get_dependency_conflicts() -> Dict[str, str]:
        """
        Find potential dependency version conflicts.

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH (d:Dependency)<-[:DEPENDS_ON]-(:File {skill_name: skill1}),
              (d2:Dependency)<-[:DEPENDS_ON]-(:File {skill_name: skill2})
        WHERE d.package_name = d2.package_name
          AND d.version_spec <> d2.version_spec
          AND skill1 < skill2
        RETURN d.package_name as package,
               collect(DISTINCT {skill: skill1, version: d.version_spec}) +
               collect(DISTINCT {skill: skill2, version: d2.version_spec}) as conflicting_versions
        ORDER BY d.package_name
        """
        return {"query": query, "params": {}}

    @staticmethod
    def get_all_skill_paths() -> Dict[str, str]:
        """
        Get all paths between skills (for visualization).

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH path = (s1:Skill)-[*1..3]-(s2:Skill)
        WHERE s1 <> s2
        WITH path,
             [n in nodes(path) | n.name] as node_names,
             [r in relationships(path) | type(r)] as rel_types
        RETURN DISTINCT node_names, rel_types
        LIMIT 100
        """
        return {"query": query, "params": {}}

    @staticmethod
    def get_skill_neighborhood(skill_name: str, depth: int = 1) -> Dict[str, str]:
        """
        Get the immediate neighborhood of a skill for visualization.

        Args:
            skill_name: Name of the skill
            depth: Depth of neighborhood (1-3)

        Returns:
            Dict with 'query' and 'params'
        """
        query = """
        MATCH path = (s:Skill {name: $skill_name})-[*0..$depth]-(node)
        WITH nodes(path) as path_nodes, relationships(path) as path_rels
        UNWIND path_nodes as node
        WITH collect(DISTINCT {
            id: id(node),
            labels: labels(node),
            properties: properties(node)
        }) as nodes,
        path_rels
        UNWIND path_rels as rel
        WITH nodes, collect(DISTINCT {
            source: id(startNode(rel)),
            target: id(endNode(rel)),
            type: type(rel),
            properties: properties(rel)
        }) as relationships
        RETURN nodes, relationships
        """
        return {"query": query, "params": {"skill_name": skill_name, "depth": depth}}
