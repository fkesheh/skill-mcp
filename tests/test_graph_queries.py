"""Tests for graph queries builder."""

import pytest
from skill_mcp.services.graph_queries import GraphQueries


class TestSkillQueries:
    """Test skill-related query builders."""

    def test_find_related_skills(self):
        """Test find_related_skills query builder."""
        result = GraphQueries.find_related_skills("test-skill", depth=3)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert isinstance(result["query"], str)
        assert len(result["query"]) > 0
        assert result["params"]["skill_name"] == "test-skill"
        assert result["params"]["depth"] == 3

    def test_find_related_skills_default_depth(self):
        """Test find_related_skills with default depth."""
        result = GraphQueries.find_related_skills("test-skill")

        assert result["params"]["depth"] == 2

    def test_get_dependency_tree(self):
        """Test get_dependency_tree query builder."""
        result = GraphQueries.get_dependency_tree("test-skill")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_find_skills_using_dependency(self):
        """Test find_skills_using_dependency query builder."""
        result = GraphQueries.find_skills_using_dependency("requests")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["package_name"] == "requests"

    def test_find_circular_dependencies(self):
        """Test find_circular_dependencies query builder."""
        result = GraphQueries.find_circular_dependencies()

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"] == {}

    def test_get_most_used_dependencies(self):
        """Test get_most_used_dependencies query builder."""
        result = GraphQueries.get_most_used_dependencies(limit=10)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["limit"] == 10

    def test_get_most_used_dependencies_default_limit(self):
        """Test get_most_used_dependencies with default limit."""
        result = GraphQueries.get_most_used_dependencies()

        assert result["params"]["limit"] == 20

    def test_find_orphaned_skills(self):
        """Test find_orphaned_skills query builder."""
        result = GraphQueries.find_orphaned_skills()

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"] == {}

    def test_get_skill_complexity_score(self):
        """Test get_skill_complexity_score query builder."""
        result = GraphQueries.get_skill_complexity_score("test-skill")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_get_import_graph(self):
        """Test get_import_graph query builder."""
        result = GraphQueries.get_import_graph("test-skill")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_find_skills_by_description(self):
        """Test find_skills_by_description query builder."""
        result = GraphQueries.find_skills_by_description("web scraping")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["search_term"] == "web scraping"

    def test_get_skill_impact_analysis(self):
        """Test get_skill_impact_analysis query builder."""
        result = GraphQueries.get_skill_impact_analysis("test-skill")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_get_execution_history(self):
        """Test get_execution_history query builder."""
        result = GraphQueries.get_execution_history("test-skill", limit=5)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"
        assert result["params"]["limit"] == 5

    def test_get_execution_history_default_limit(self):
        """Test get_execution_history with default limit."""
        result = GraphQueries.get_execution_history("test-skill")

        assert result["params"]["limit"] == 10

    def test_find_similar_skills(self):
        """Test find_similar_skills query builder."""
        result = GraphQueries.find_similar_skills("test-skill", limit=3)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"
        assert result["params"]["limit"] == 3

    def test_find_similar_skills_default_limit(self):
        """Test find_similar_skills with default limit."""
        result = GraphQueries.find_similar_skills("test-skill")

        assert result["params"]["limit"] == 5

    def test_get_dependency_conflicts(self):
        """Test get_dependency_conflicts query builder."""
        result = GraphQueries.get_dependency_conflicts()

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"] == {}

    def test_get_all_skill_paths(self):
        """Test get_all_skill_paths query builder."""
        result = GraphQueries.get_all_skill_paths()

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"] == {}

    def test_get_skill_neighborhood(self):
        """Test get_skill_neighborhood query builder."""
        result = GraphQueries.get_skill_neighborhood("test-skill", depth=2)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"
        assert result["params"]["depth"] == 2

    def test_get_skill_neighborhood_default_depth(self):
        """Test get_skill_neighborhood with default depth."""
        result = GraphQueries.get_skill_neighborhood("test-skill")

        assert result["params"]["depth"] == 1


class TestKnowledgeQueries:
    """Test knowledge-related query builders."""

    def test_list_all_knowledge(self):
        """Test list_all_knowledge query builder."""
        result = GraphQueries.list_all_knowledge(limit=100)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["limit"] == 100

    def test_list_all_knowledge_default_limit(self):
        """Test list_all_knowledge with default limit."""
        result = GraphQueries.list_all_knowledge()

        assert result["params"]["limit"] == 50

    def test_get_knowledge_by_id(self):
        """Test get_knowledge_by_id query builder."""
        result = GraphQueries.get_knowledge_by_id("test-knowledge")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["knowledge_id"] == "test-knowledge"

    def test_search_knowledge(self):
        """Test search_knowledge query builder."""
        result = GraphQueries.search_knowledge("python", limit=15)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["search_term"] == "python"
        assert result["params"]["limit"] == 15

    def test_search_knowledge_default_limit(self):
        """Test search_knowledge with default limit."""
        result = GraphQueries.search_knowledge("python")

        assert result["params"]["limit"] == 20

    def test_get_knowledge_by_category(self):
        """Test get_knowledge_by_category query builder."""
        result = GraphQueries.get_knowledge_by_category("tutorial")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["category"] == "tutorial"

    def test_get_knowledge_by_tag(self):
        """Test get_knowledge_by_tag query builder."""
        result = GraphQueries.get_knowledge_by_tag("python")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["tag"] == "python"

    def test_find_knowledge_about_skill(self):
        """Test find_knowledge_about_skill query builder."""
        result = GraphQueries.find_knowledge_about_skill("test-skill")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["skill_name"] == "test-skill"

    def test_find_skills_for_knowledge(self):
        """Test find_skills_for_knowledge query builder."""
        result = GraphQueries.find_skills_for_knowledge("test-knowledge")

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["knowledge_id"] == "test-knowledge"

    def test_find_related_knowledge(self):
        """Test find_related_knowledge query builder."""
        result = GraphQueries.find_related_knowledge("test-knowledge", limit=5)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["knowledge_id"] == "test-knowledge"
        assert result["params"]["limit"] == 5

    def test_find_related_knowledge_default_limit(self):
        """Test find_related_knowledge with default limit."""
        result = GraphQueries.find_related_knowledge("test-knowledge")

        assert result["params"]["limit"] == 10

    def test_get_knowledge_network(self):
        """Test get_knowledge_network query builder."""
        result = GraphQueries.get_knowledge_network(limit=100)

        assert isinstance(result, dict)
        assert "query" in result
        assert "params" in result
        assert result["params"]["limit"] == 100

    def test_get_knowledge_network_default_limit(self):
        """Test get_knowledge_network with default limit."""
        result = GraphQueries.get_knowledge_network()

        assert result["params"]["limit"] == 50


class TestQueryStructure:
    """Test general query structure and validation."""

    def test_all_queries_return_dict_with_query_and_params(self):
        """Test that all query methods return proper structure."""
        # Test a sample of different query methods
        queries_to_test = [
            GraphQueries.find_related_skills("test"),
            GraphQueries.get_dependency_tree("test"),
            GraphQueries.find_circular_dependencies(),
            GraphQueries.list_all_knowledge(),
            GraphQueries.search_knowledge("test"),
        ]

        for result in queries_to_test:
            assert isinstance(result, dict)
            assert "query" in result
            assert "params" in result
            assert isinstance(result["query"], str)
            assert isinstance(result["params"], dict)
            assert len(result["query"]) > 0

    def test_queries_contain_cypher_keywords(self):
        """Test that queries contain valid Cypher keywords."""
        # Sample queries to verify they're actual Cypher
        result = GraphQueries.find_related_skills("test")
        query = result["query"]

        # Should contain common Cypher keywords
        assert "MATCH" in query or "match" in query.lower()
        assert "RETURN" in query or "return" in query.lower()

    def test_parameterized_queries_use_dollar_syntax(self):
        """Test that parameterized queries use $param syntax."""
        result = GraphQueries.find_related_skills("test")
        query = result["query"]

        # Should use $skill_name and $depth parameters
        assert "$skill_name" in query
        assert "$depth" in query

    def test_knowledge_queries_reference_knowledge_label(self):
        """Test that knowledge queries reference the Knowledge label."""
        result = GraphQueries.list_all_knowledge()
        query = result["query"]

        # Should reference Knowledge nodes
        assert "Knowledge" in query

    def test_skill_queries_reference_skill_label(self):
        """Test that skill queries reference the Skill label."""
        result = GraphQueries.find_related_skills("test")
        query = result["query"]

        # Should reference Skill nodes
        assert "Skill" in query
