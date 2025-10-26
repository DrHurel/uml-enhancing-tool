"""Knowledge graph module for transforming UML diagrams into graph representations."""

from typing import Dict, List, Set
import networkx as nx
from dataclasses import dataclass


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""

    id: str
    type: str  # 'class', 'attribute', 'method'
    properties: Dict


class KnowledgeGraph:
    """Knowledge graph representation of UML diagrams."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._node_counter = 0

    def from_uml_model(self, classes: Dict, relationships: List) -> nx.DiGraph:
        """
        Transform UML model into a knowledge graph.

        Args:
            classes: Dictionary of UML classes
            relationships: List of UML relationships

        Returns:
            NetworkX directed graph representing the knowledge graph
        """
        # Add class nodes
        for class_name, uml_class in classes.items():
            self.graph.add_node(
                class_name,
                type="class",
                attributes=uml_class.attributes,
                methods=uml_class.methods,
                stereotypes=uml_class.stereotypes,
            )

            # Add attribute nodes
            for attr in uml_class.attributes:
                attr_id = f"{class_name}_{attr}_{self._get_next_id()}"
                self.graph.add_node(
                    attr_id, type="attribute", value=attr, parent_class=class_name
                )
                self.graph.add_edge(class_name, attr_id, relation="has_attribute")

            # Add method nodes
            for method in uml_class.methods:
                method_id = f"{class_name}_{method}_{self._get_next_id()}"
                self.graph.add_node(
                    method_id, type="method", value=method, parent_class=class_name
                )
                self.graph.add_edge(class_name, method_id, relation="has_method")

        # Add relationship edges
        for rel in relationships:
            self.graph.add_edge(
                rel.source,
                rel.target,
                relation=rel.relationship_type,
                cardinality_source=rel.cardinality_source,
                cardinality_target=rel.cardinality_target,
                label=rel.label,
            )

        return self.graph

    def _get_next_id(self) -> int:
        """Generate unique node IDs."""
        self._node_counter += 1
        return self._node_counter

    def export_for_fca(self, output_path: str):
        """
        Export knowledge graph in a format suitable for FCA4J analysis.

        Args:
            output_path: Path to save the exported data
        """
        # Create formal context (objects × attributes matrix)
        context = []

        # Extract classes as objects
        classes = [
            n for n, d in self.graph.nodes(data=True) if d.get("type") == "class"
        ]

        # Extract all unique attributes AND methods as features
        features = set()
        for node, data in self.graph.nodes(data=True):
            if data.get("type") in ["attribute", "method"]:
                features.add(data.get("value"))

        # Build the formal context
        for cls in classes:
            row = {"object": cls}

            # Get attributes and methods of this class
            cls_features = set()
            for neighbor in self.graph.neighbors(cls):
                node_data = self.graph.nodes[neighbor]
                if node_data.get("type") in ["attribute", "method"]:
                    cls_features.add(node_data.get("value"))

            # Mark presence/absence of each feature
            for feature in features:
                row[feature] = feature in cls_features

            context.append(row)

        # Save to file (CSV format for FCA4J)
        # FCA4J CSV format: rows = objects, columns = attributes
        # We want: objects = classes, attributes = UML attributes
        import csv

        with open(output_path, "w", newline="") as f:
            if context and features:
                sorted_features = sorted(list(features))
                sorted_classes = sorted(classes)

                # Write header: empty first cell, then attribute names as columns
                fieldnames = [""] + sorted_features
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                # Write each class as a row
                for cls in sorted_classes:
                    # Find which attributes this class has
                    cls_attrs = set()
                    for row in context:
                        if row["object"] == cls:
                            for feature in features:
                                if row.get(feature, False):
                                    cls_attrs.add(feature)
                            break

                    # Build the row
                    fca_row = {"": cls}
                    for feature in sorted_features:
                        fca_row[feature] = "X" if feature in cls_attrs else ""
                    writer.writerow(fca_row)

        return output_path

    def get_class_features(self, class_name: str) -> Dict:
        """
        Get all features (attributes, methods, relationships) of a class.

        Args:
            class_name: Name of the class

        Returns:
            Dictionary containing class features
        """
        if class_name not in self.graph:
            return {}

        node_data = self.graph.nodes[class_name]

        # Get relationships
        relationships = []
        for source, target, data in self.graph.edges(class_name, data=True):
            if data.get("relation") not in ["has_attribute", "has_method"]:
                relationships.append(
                    {
                        "target": target,
                        "type": data.get("relation"),
                        "cardinality": data.get("cardinality_target"),
                    }
                )

        return {
            "attributes": node_data.get("attributes", []),
            "methods": node_data.get("methods", []),
            "relationships": relationships,
        }
