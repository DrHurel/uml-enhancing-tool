"""Test configuration and fixtures."""

import pytest
import os
from pathlib import Path


@pytest.fixture
def sample_plantuml():
    """Sample PlantUML diagram for testing."""
    return """@startuml
class Animal {
  +name: String
  +age: int
  +eat()
  +sleep()
}

class Dog {
  +name: String
  +age: int
  +breed: String
  +bark()
  +eat()
  +sleep()
}

class Cat {
  +name: String
  +age: int
  +color: String
  +meow()
  +eat()
  +sleep()
}

class Vehicle {
  +speed: int
  +start()
  +stop()
}

class Car {
  +speed: int
  +doors: int
  +start()
  +stop()
}

Dog --|> Animal
Cat --|> Animal
Car --|> Vehicle

@enduml"""


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def sample_uml_classes():
    """Sample parsed UML classes."""
    from src.parser import UMLClass

    return {
        "Dog": UMLClass(
            name="Dog",
            attributes=["+name: String", "+age: int"],
            methods=["+bark()", "+eat()"],
        ),
        "Cat": UMLClass(
            name="Cat",
            attributes=["+name: String", "+age: int"],
            methods=["+meow()", "+eat()"],
        ),
    }


@pytest.fixture
def sample_uml_relationships():
    """Sample UML relationships."""
    from src.parser import UMLRelationship

    return [
        UMLRelationship(source="Dog", target="Animal", relationship_type="inheritance"),
        UMLRelationship(source="Cat", target="Animal", relationship_type="inheritance"),
    ]
