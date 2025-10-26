"""PlantUML generator module for creating enhanced diagrams."""

from typing import List, Dict
import os


class PlantUMLGenerator:
    """Generator for enhanced PlantUML diagrams."""

    def __init__(self):
        self.output_lines = []

    def generate(
        self,
        original_classes: Dict,
        original_relationships: List,
        abstract_classes: List,
        output_path: str,
    ) -> str:
        """
        Generate enhanced PlantUML diagram with abstract classes.

        Args:
            original_classes: Original UML classes
            original_relationships: Original relationships
            abstract_classes: New abstract classes to add
            output_path: Path to save the generated diagram

        Returns:
            Path to the generated diagram file
        """
        self.output_lines = []

        # Build a mapping of child classes to their inherited features
        inherited_features = self._build_inheritance_map(abstract_classes)

        # Start PlantUML
        self._add_line("@startuml")
        self._add_line("")

        # Add abstract classes first
        self._add_line("' Abstract Classes (Generated)")
        for abstract_class in abstract_classes:
            self._generate_abstract_class(abstract_class)

        self._add_line("")

        # Add original classes (with inherited features removed)
        self._add_line("' Original Classes")
        for class_name, uml_class in original_classes.items():
            self._generate_class(uml_class, inherited_features.get(class_name, set()))

        self._add_line("")

        # Add inheritance relationships to abstract classes
        self._add_line("' Inheritance Relationships to Abstract Classes")
        for abstract_class in abstract_classes:
            for child_class in abstract_class.extent:
                self._add_line(f"{child_class} --|> {abstract_class.suggested_name}")

        self._add_line("")

        # Add original relationships
        self._add_line("' Original Relationships")
        for rel in original_relationships:
            self._generate_relationship(rel)

        # End PlantUML
        self._add_line("")
        self._add_line("@enduml")

        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(self.output_lines))

        return output_path

    def _build_inheritance_map(self, abstract_classes: List) -> Dict[str, set]:
        """
        Build a mapping of class names to their inherited features.

        Args:
            abstract_classes: List of abstract classes

        Returns:
            Dict mapping class name to set of inherited features
        """
        inheritance_map = {}

        for abstract_class in abstract_classes:
            # Each class in the extent inherits all features from the intent
            for child_class in abstract_class.extent:
                if child_class not in inheritance_map:
                    inheritance_map[child_class] = set()
                inheritance_map[child_class].update(abstract_class.intent)

        return inheritance_map

    def _generate_abstract_class(self, abstract_class):
        """Generate PlantUML code for an abstract class."""
        self._add_line(f"abstract class {abstract_class.suggested_name} {{")

        # Add common attributes from intent
        for attribute in abstract_class.intent:
            self._add_line(f"  {attribute}")

        self._add_line("}")

    def _generate_class(self, uml_class, inherited_features: set = None):
        """
        Generate PlantUML code for a regular class.

        Args:
            uml_class: The UML class to generate
            inherited_features: Set of features inherited from abstract classes
        """
        if inherited_features is None:
            inherited_features = set()

        self._add_line(f"class {uml_class.name} {{")

        # Add attributes (excluding inherited ones)
        for attr in uml_class.attributes:
            if attr not in inherited_features:
                self._add_line(f"  {attr}")

        # Add methods (excluding inherited ones)
        for method in uml_class.methods:
            if method not in inherited_features:
                self._add_line(f"  {method}")

        self._add_line("}")

    def _generate_relationship(self, relationship):
        """Generate PlantUML code for a relationship."""
        # Map relationship types to PlantUML syntax
        symbol_map = {
            "inheritance": "--|>",
            "composition": "*--",
            "aggregation": "o--",
            "association": "--",
        }

        symbol = symbol_map.get(relationship.relationship_type, "--")

        # Build relationship line with cardinality
        if relationship.cardinality_source or relationship.cardinality_target:
            # Format: Source "cardinality" -- "cardinality" Target
            card_source = (
                f'"{relationship.cardinality_source}"'
                if relationship.cardinality_source
                else ""
            )
            card_target = (
                f'"{relationship.cardinality_target}"'
                if relationship.cardinality_target
                else ""
            )

            if card_source and card_target:
                line = f"{relationship.source} {card_source} {symbol} {card_target} {relationship.target}"
            elif card_source:
                line = f"{relationship.source} {card_source} {symbol} {relationship.target}"
            elif card_target:
                line = f"{relationship.source} {symbol} {card_target} {relationship.target}"
            else:
                line = f"{relationship.source} {symbol} {relationship.target}"
        else:
            line = f"{relationship.source} {symbol} {relationship.target}"

        # Add label if present
        if relationship.label:
            line += f" : {relationship.label}"

        self._add_line(line)

    def _add_line(self, line: str):
        """Add a line to the output."""
        self.output_lines.append(line)

    def generate_comparison_report(
        self, original_diagram_path: str, enhanced_diagram_path: str, output_path: str
    ):
        """
        Generate a comparison report between original and enhanced diagrams.

        Args:
            original_diagram_path: Path to original diagram
            enhanced_diagram_path: Path to enhanced diagram
            output_path: Path to save the report
        """
        report_lines = []

        report_lines.append("# UML Diagram Enhancement Report")
        report_lines.append("")
        report_lines.append(f"**Original Diagram**: {original_diagram_path}")
        report_lines.append(f"**Enhanced Diagram**: {enhanced_diagram_path}")
        report_lines.append("")
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append("The enhanced diagram includes the following improvements:")
        report_lines.append("- Added abstract classes based on formal concept analysis")
        report_lines.append(
            "- Identified common patterns and extracted them into superclasses"
        )
        report_lines.append("- Improved class hierarchy and reusability")
        report_lines.append("")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(report_lines))
