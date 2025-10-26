"""Unit tests for PlantUML generator."""

import pytest
import os
from src.generator import PlantUMLGenerator
from src.parser import UMLClass, UMLRelationship
from src.llm_naming import AbstractClass


@pytest.mark.unit
class TestPlantUMLGenerator:
    """Test suite for PlantUML generator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = PlantUMLGenerator()
        assert generator.output_lines == []

    def test_generate_simple_diagram(self, temp_output_dir):
        """Test generating a simple diagram."""
        generator = PlantUMLGenerator()

        classes = {
            "Dog": UMLClass(name="Dog", attributes=["+name"], methods=["+bark()"])
        }
        relationships = []
        abstract_classes = []

        output_path = os.path.join(temp_output_dir, "output.puml")
        result = generator.generate(
            classes, relationships, abstract_classes, output_path
        )

        assert os.path.exists(result)

        with open(result, "r") as f:
            content = f.read()
            assert "@startuml" in content
            assert "@enduml" in content
            assert "Dog" in content

    def test_generate_with_abstract_class(self, temp_output_dir):
        """Test generating diagram with abstract classes."""
        generator = PlantUMLGenerator()

        classes = {
            "Dog": UMLClass(name="Dog", attributes=["+name"], methods=["+bark()"]),
            "Cat": UMLClass(name="Cat", attributes=["+name"], methods=["+meow()"]),
        }
        relationships = []
        abstract_classes = [
            AbstractClass(
                extent=["Dog", "Cat"], intent=["+name"], suggested_name="Animal"
            )
        ]

        output_path = os.path.join(temp_output_dir, "enhanced.puml")
        result = generator.generate(
            classes, relationships, abstract_classes, output_path
        )

        assert os.path.exists(result)

        with open(result, "r") as f:
            content = f.read()
            assert "abstract class Animal" in content
            assert "Dog --|> Animal" in content
            assert "Cat --|> Animal" in content

    def test_generate_with_relationships(self, temp_output_dir):
        """Test generating diagram with relationships."""
        generator = PlantUMLGenerator()

        classes = {
            "Dog": UMLClass(name="Dog", attributes=[], methods=[]),
            "Animal": UMLClass(name="Animal", attributes=[], methods=[]),
        }
        relationships = [
            UMLRelationship(
                source="Dog", target="Animal", relationship_type="inheritance"
            )
        ]
        abstract_classes = []

        output_path = os.path.join(temp_output_dir, "with_rel.puml")
        result = generator.generate(
            classes, relationships, abstract_classes, output_path
        )

        with open(result, "r") as f:
            content = f.read()
            assert "--|>" in content

    def test_generate_comparison_report(self, temp_output_dir):
        """Test generating comparison report."""
        generator = PlantUMLGenerator()

        original = os.path.join(temp_output_dir, "original.puml")
        enhanced = os.path.join(temp_output_dir, "enhanced.puml")
        report = os.path.join(temp_output_dir, "report.md")

        # Create dummy files
        open(original, "w").close()
        open(enhanced, "w").close()

        generator.generate_comparison_report(original, enhanced, report)

        assert os.path.exists(report)

        with open(report, "r") as f:
            content = f.read()
            assert "Enhancement Report" in content

    def test_deduplicate_abstract_class_names_no_duplicates(self):
        """Test deduplication with no duplicate names."""
        generator = PlantUMLGenerator()

        abstract_classes = [
            AbstractClass(
                extent=["Class1", "Class2"],
                intent=["method1()"],
                suggested_name="Abstract1",
                relevance_score=50.0,
            ),
            AbstractClass(
                extent=["Class3"],
                intent=["method2()"],
                suggested_name="Abstract2",
                relevance_score=60.0,
            ),
        ]

        result = generator._deduplicate_abstract_class_names(abstract_classes)

        assert len(result) == 2
        assert result[0].suggested_name == "Abstract1"
        assert result[1].suggested_name == "Abstract2"

    def test_deduplicate_abstract_class_names_with_duplicates(self):
        """Test deduplication with duplicate names - should merge by relevance."""
        generator = PlantUMLGenerator()

        abstract_classes = [
            AbstractClass(
                extent=["Class1", "Class2"],
                intent=["method1()"],
                suggested_name="Manager",
                relevance_score=50.0,
            ),
            AbstractClass(
                extent=["Class3", "Class4"],
                intent=["method2()"],
                suggested_name="Manager",
                relevance_score=75.0,
            ),
            AbstractClass(
                extent=["Class5"],
                intent=["method3()"],
                suggested_name="Manager",
                relevance_score=60.0,
            ),
        ]

        result = generator._deduplicate_abstract_class_names(abstract_classes)

        # Should merge into single Manager with highest relevance (75.0)
        assert len(result) == 1
        assert result[0].suggested_name == "Manager"
        assert result[0].relevance_score == 75.0
        # Should contain all extents
        assert set(result[0].extent) == {
            "Class1",
            "Class2",
            "Class3",
            "Class4",
            "Class5",
        }
        # Should contain all intents
        assert set(result[0].intent) == {"method1()", "method2()", "method3()"}

    def test_deduplicate_abstract_class_names_mixed(self):
        """Test deduplication with mix of unique and duplicate names."""
        generator = PlantUMLGenerator()

        abstract_classes = [
            AbstractClass(
                extent=["A"],
                intent=["m1()"],
                suggested_name="Unique",
                relevance_score=50.0,
            ),
            AbstractClass(
                extent=["B"],
                intent=["m2()"],
                suggested_name="Duplicate",
                relevance_score=60.0,
            ),
            AbstractClass(
                extent=["C"],
                intent=["m3()"],
                suggested_name="Duplicate",
                relevance_score=70.0,
            ),
        ]

        result = generator._deduplicate_abstract_class_names(abstract_classes)

        assert len(result) == 2
        names = [r.suggested_name for r in result]
        assert "Unique" in names
        assert "Duplicate" in names

        # Find the merged duplicate
        duplicate = next(r for r in result if r.suggested_name == "Duplicate")
        assert set(duplicate.extent) == {"B", "C"}
        assert set(duplicate.intent) == {"m2()", "m3()"}
        assert duplicate.relevance_score == 70.0  # Higher score wins
