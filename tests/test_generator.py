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
