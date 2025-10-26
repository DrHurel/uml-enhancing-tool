"""Unit tests for PlantUML parser."""

import pytest
from src.parser import PlantUMLParser, UMLClass, UMLRelationship


@pytest.mark.unit
class TestPlantUMLParser:
    """Test suite for PlantUML parser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = PlantUMLParser()
        assert parser.classes == {}
        assert parser.relationships == []

    def test_parse_simple_class(self):
        """Test parsing a simple class."""
        parser = PlantUMLParser()
        plantuml = """@startuml
class Animal {
  +name: String
  +eat()
}
@enduml"""

        result = parser.parse(plantuml)

        assert "Animal" in result["classes"]
        assert result["classes"]["Animal"].name == "Animal"
        assert "+name: String" in result["classes"]["Animal"].attributes
        assert "+eat()" in result["classes"]["Animal"].methods

    def test_parse_multiple_classes(self, sample_plantuml):
        """Test parsing multiple classes."""
        parser = PlantUMLParser()
        result = parser.parse(sample_plantuml)

        assert len(result["classes"]) > 0
        assert "Dog" in result["classes"]
        assert "Cat" in result["classes"]

    def test_parse_inheritance_relationship(self):
        """Test parsing inheritance relationships."""
        parser = PlantUMLParser()
        plantuml = """@startuml
class Animal {
}
class Dog {
}
Dog --|> Animal
@enduml"""

        result = parser.parse(plantuml)

        assert len(result["relationships"]) > 0
        rel = result["relationships"][0]
        assert rel.source == "Dog"
        assert rel.target == "Animal"
        assert rel.relationship_type == "inheritance"

    def test_parse_composition_relationship(self):
        """Test parsing composition relationships."""
        parser = PlantUMLParser()
        plantuml = """@startuml
class Engine {
}
class Car {
}
Car *-- Engine
@enduml"""

        result = parser.parse(plantuml)

        assert len(result["relationships"]) > 0
        rel = result["relationships"][0]
        assert rel.relationship_type == "composition"

    def test_parse_with_cardinality(self):
        """Test parsing relationships with cardinality."""
        parser = PlantUMLParser()
        plantuml = """@startuml
class Student {
}
class Course {
}
Student "1..*" -- "1..*" Course
@enduml"""

        result = parser.parse(plantuml)

        # Basic parsing should work, cardinality extraction can be enhanced
        assert len(result["relationships"]) > 0

    def test_parse_empty_diagram(self):
        """Test parsing an empty diagram."""
        parser = PlantUMLParser()
        plantuml = """@startuml
@enduml"""

        result = parser.parse(plantuml)

        assert result["classes"] == {}
        assert result["relationships"] == []

    def test_uml_class_dataclass(self):
        """Test UMLClass dataclass."""
        uml_class = UMLClass(
            name="TestClass", attributes=["+attr1"], methods=["+method1()"]
        )

        assert uml_class.name == "TestClass"
        assert len(uml_class.attributes) == 1
        assert len(uml_class.methods) == 1
        assert uml_class.stereotypes == []

    def test_uml_relationship_dataclass(self):
        """Test UMLRelationship dataclass."""
        rel = UMLRelationship(
            source="ClassA",
            target="ClassB",
            relationship_type="association",
            cardinality_source="1",
            cardinality_target="*",
        )

        assert rel.source == "ClassA"
        assert rel.target == "ClassB"
        assert rel.relationship_type == "association"
        assert rel.cardinality_source == "1"
        assert rel.cardinality_target == "*"
