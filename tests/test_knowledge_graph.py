"""Unit tests for knowledge graph module."""

import pytest
import networkx as nx
from src.knowledge_graph import KnowledgeGraph
from src.parser import UMLClass, UMLRelationship


@pytest.mark.unit
class TestKnowledgeGraph:
    """Test suite for knowledge graph."""

    def test_initialization(self):
        """Test knowledge graph initialization."""
        kg = KnowledgeGraph()
        assert isinstance(kg.graph, nx.DiGraph)
        assert kg.graph.number_of_nodes() == 0

    def test_from_uml_model_simple(self):
        """Test creating knowledge graph from simple UML model."""
        kg = KnowledgeGraph()

        classes = {
            "Animal": UMLClass(
                name="Animal", attributes=["+name: String"], methods=["+eat()"]
            )
        }
        relationships = []

        graph = kg.from_uml_model(classes, relationships)

        assert "Animal" in graph.nodes()
        assert graph.nodes["Animal"]["type"] == "class"

    def test_from_uml_model_with_relationships(
        self, sample_uml_classes, sample_uml_relationships
    ):
        """Test creating knowledge graph with relationships."""
        kg = KnowledgeGraph()

        graph = kg.from_uml_model(sample_uml_classes, sample_uml_relationships)

        # Check that classes are added
        assert "Dog" in graph.nodes()
        assert "Cat" in graph.nodes()

        # Check that attribute nodes are created
        attribute_nodes = [
            n for n, d in graph.nodes(data=True) if d.get("type") == "attribute"
        ]
        assert len(attribute_nodes) > 0

    def test_export_for_fca(self, sample_uml_classes, temp_output_dir):
        """Test exporting knowledge graph for FCA."""
        import os

        kg = KnowledgeGraph()
        kg.from_uml_model(sample_uml_classes, [])

        output_path = os.path.join(temp_output_dir, "context.csv")
        result_path = kg.export_for_fca(output_path)

        assert os.path.exists(result_path)

        # Check CSV content - should have class names and attributes
        with open(result_path, "r") as f:
            content = f.read()
            # CSV format has classes as rows, attributes as columns
            assert "Dog" in content or "Cat" in content
            assert "X" in content  # At least some incidence markers

    def test_get_class_features(self):
        """Test getting class features."""
        kg = KnowledgeGraph()

        classes = {
            "Dog": UMLClass(
                name="Dog", attributes=["+name: String"], methods=["+bark()"]
            )
        }

        kg.from_uml_model(classes, [])
        features = kg.get_class_features("Dog")

        assert "attributes" in features
        assert "methods" in features
        assert "+name: String" in features["attributes"]
        assert "+bark()" in features["methods"]

    def test_get_class_features_nonexistent(self):
        """Test getting features for non-existent class."""
        kg = KnowledgeGraph()
        features = kg.get_class_features("NonExistent")

        assert features == {}
