"""PlantUML parser module for extracting UML diagram elements."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class UMLClass:
    """Represents a UML class."""

    name: str
    attributes: List[str]
    methods: List[str]
    stereotypes: List[str] = None

    def __post_init__(self):
        if self.stereotypes is None:
            self.stereotypes = []


@dataclass
class UMLRelationship:
    """Represents a UML relationship between classes."""

    source: str
    target: str
    relationship_type: str  # inheritance, composition, aggregation, association
    cardinality_source: Optional[str] = None
    cardinality_target: Optional[str] = None
    label: Optional[str] = None


class PlantUMLParser:
    """Parser for PlantUML diagrams."""

    def __init__(self):
        self.classes: Dict[str, UMLClass] = {}
        self.relationships: List[UMLRelationship] = []

    def parse(self, plantuml_content: str) -> Dict:
        """
        Parse PlantUML content and extract classes and relationships.

        Args:
            plantuml_content: The PlantUML diagram as a string

        Returns:
            Dictionary containing parsed classes and relationships
        """
        self.classes = {}
        self.relationships = []

        lines = plantuml_content.strip().split("\n")
        current_class = None

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("'") or line.startswith("@"):
                continue

            # Parse class declarations
            if line.startswith("class "):
                current_class = self._parse_class_declaration(line)
            elif line == "}":
                current_class = None
            elif current_class and (
                line.startswith("+") or line.startswith("-") or line.startswith("#")
            ):
                self._parse_class_member(current_class, line)
            # Parse relationships
            elif any(
                rel in line
                for rel in ["--|>", "--*", "--o", "--", "<|--", "*--", "o--"]
            ):
                self._parse_relationship(line)

        return {"classes": self.classes, "relationships": self.relationships}

    def _parse_class_declaration(self, line: str) -> str:
        """Parse a class declaration line."""
        parts = line.replace("class ", "").replace("{", "").strip().split()
        class_name = parts[0]

        self.classes[class_name] = UMLClass(name=class_name, attributes=[], methods=[])

        return class_name

    def _parse_class_member(self, class_name: str, line: str):
        """Parse class attributes and methods."""
        if "(" in line:  # Method
            self.classes[class_name].methods.append(line)
        else:  # Attribute
            self.classes[class_name].attributes.append(line)

    def _parse_relationship(self, line: str):
        """Parse relationship between classes with cardinality support."""
        import re

        for rel_type, symbol in [
            ("inheritance", "--|>"),
            ("inheritance", "<|--"),
            ("composition", "--*"),
            ("composition", "*--"),
            ("aggregation", "--o"),
            ("aggregation", "o--"),
            ("association", "-->"),  # Check --> before --
            ("association", "<--"),
            ("association", "--"),  # Generic association (must be last)
        ]:
            if symbol in line:
                parts = line.split(symbol)
                if len(parts) == 2:
                    # Parse source side: "ClassName" or "ClassName "cardinality""
                    source_part = parts[0].strip()
                    target_part = parts[1].strip()

                    # Extract source class name and cardinality
                    source_match = re.match(r'(\w+)(?:\s+"([^"]+)")?', source_part)
                    source = (
                        source_match.group(1)
                        if source_match
                        else source_part.split()[0]
                    )
                    cardinality_source = (
                        source_match.group(2)
                        if source_match and source_match.group(2)
                        else None
                    )

                    # Extract target class name, cardinality, and label
                    # Pattern: ["cardinality"] ClassName [: label]
                    # Handle both: 'ClassName : "label"' and '"card" ClassName : label'
                    target_match = re.match(
                        r'(?:"([^"]+)"\s+)?(\w+)(?:\s*:\s*(?:"([^"]+)"|(.+)))?',
                        target_part,
                    )
                    if target_match:
                        cardinality_target = target_match.group(1)
                        target = target_match.group(2)
                        # Label can be quoted (group 3) or unquoted (group 4)
                        label = target_match.group(3) or target_match.group(4)
                        if label:
                            label = label.strip()
                    else:
                        target = target_part.split()[0]
                        cardinality_target = None
                        label = None

                    self.relationships.append(
                        UMLRelationship(
                            source=source,
                            target=target,
                            relationship_type=rel_type,
                            cardinality_source=cardinality_source,
                            cardinality_target=cardinality_target,
                            label=label,
                        )
                    )
                    break
