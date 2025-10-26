"""Unit tests for FCA analyzer."""

import pytest
import os
from src.fca_analyzer import FCAAnalyzer, FormalConcept


@pytest.mark.unit
class TestFCAAnalyzer:
    """Test suite for FCA analyzer."""

    def test_initialization(self):
        """Test FCA analyzer initialization."""
        analyzer = FCAAnalyzer()
        assert analyzer.concepts == []

    def test_formal_concept_dataclass(self):
        """Test FormalConcept dataclass."""
        concept = FormalConcept(extent={"Dog", "Cat"}, intent={"name", "age"})

        assert len(concept.extent) == 2
        assert len(concept.intent) == 2
        assert concept.relevance_score == 0.0

    @pytest.mark.slow
    def test_fallback_fca_analysis(self, temp_output_dir):
        """Test fallback FCA analysis."""
        # Create a simple context file
        context_file = os.path.join(temp_output_dir, "context.csv")
        with open(context_file, "w") as f:
            f.write("object,attr1,attr2\n")
            f.write("Dog,True,True\n")
            f.write("Cat,True,False\n")

        analyzer = FCAAnalyzer(fca4j_path="nonexistent.jar")
        concepts = analyzer._fallback_fca_analysis(context_file)

        assert len(concepts) > 0

    def test_calculate_relevance_scores(self):
        """Test relevance score calculation."""
        analyzer = FCAAnalyzer()

        analyzer.concepts = [
            FormalConcept(extent={"A", "B"}, intent={"x", "y"}),
            FormalConcept(extent={"A"}, intent={"x"}),
        ]

        analyzer._calculate_relevance_scores()

        # First concept should have higher relevance
        assert analyzer.concepts[0].relevance_score > 0

    def test_filter_relevant_concepts(self):
        """Test filtering relevant concepts."""
        analyzer = FCAAnalyzer()

        analyzer.concepts = [
            FormalConcept(extent={"A", "B", "C"}, intent={"x"}, relevance_score=80.0),
            FormalConcept(extent={"A"}, intent={"x"}, relevance_score=20.0),
            FormalConcept(extent={"A", "B"}, intent={"x", "y"}, relevance_score=60.0),
        ]

        relevant = analyzer.filter_relevant_concepts(
            min_relevance=50.0, min_extent_size=2
        )

        assert len(relevant) == 2
        assert all(len(c.extent) >= 2 for c in relevant)
        assert all(c.relevance_score >= 50.0 for c in relevant)

    def test_export_concepts(self, temp_output_dir):
        """Test exporting concepts to JSON."""
        import json

        analyzer = FCAAnalyzer()
        analyzer.concepts = [
            FormalConcept(extent={"A", "B"}, intent={"x"}, relevance_score=75.0)
        ]

        output_path = os.path.join(temp_output_dir, "concepts.json")
        analyzer.export_concepts(output_path)

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["relevance_score"] == 75.0

    def test_calculate_relevance_scores_with_boost(self):
        """Test relevance score calculation with intent boost."""
        analyzer = FCAAnalyzer()

        # Concept with 3+ intents should get 1.5x boost
        analyzer.concepts = [
            FormalConcept(extent={"A", "B"}, intent={"x", "y", "z", "w"}),  # 4 intents
            FormalConcept(extent={"A", "B"}, intent={"x", "y"}),  # 2 intents
        ]

        analyzer._calculate_relevance_scores()

        # First concept should have higher relevance due to boost
        assert (
            analyzer.concepts[0].relevance_score > analyzer.concepts[1].relevance_score
        )

    def test_filter_relevant_concepts_edge_cases(self):
        """Test filtering with edge cases."""
        analyzer = FCAAnalyzer()

        analyzer.concepts = [
            FormalConcept(
                extent={"A"}, intent={"x"}, relevance_score=100.0
            ),  # Too small extent
            FormalConcept(
                extent={"A", "B"}, intent={"x"}, relevance_score=10.0
            ),  # Too low relevance
            FormalConcept(
                extent={"A", "B", "C"}, intent={"x", "y"}, relevance_score=75.0
            ),  # Good
        ]

        relevant = analyzer.filter_relevant_concepts(
            min_relevance=50.0, min_extent_size=2
        )

        assert len(relevant) == 1
        assert len(relevant[0].extent) == 3

    def test_analyze_with_xml_parsing(self, temp_output_dir):
        """Test that analyze method handles XML parsing correctly."""
        analyzer = FCAAnalyzer()

        # Create a simple context
        context_file = os.path.join(temp_output_dir, "simple.csv")
        with open(context_file, "w") as f:
            f.write("object,attr1,attr2\n")
            f.write("A,True,True\n")
            f.write("B,True,False\n")
            f.write("C,True,True\n")

        # Run analyze (will use fallback since FCA4J likely not available in test)
        concepts = analyzer.analyze(context_file, temp_output_dir)

        assert isinstance(concepts, list)
        assert len(concepts) > 0
        assert all(isinstance(c, FormalConcept) for c in concepts)
