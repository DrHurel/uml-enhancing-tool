"""FCA analyzer module for extracting formal concepts using FCA4J."""

import subprocess
import json
import os
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class FormalConcept:
    """Represents a formal concept from FCA."""

    extent: Set[str]  # Set of objects
    intent: Set[str]  # Set of attributes
    relevance_score: float = 0.0


class FCAAnalyzer:
    """Analyzer for Formal Concept Analysis using FCA4J."""

    def __init__(self, fca4j_path: str = "fca4j-cli-0.4.4.jar"):
        """
        Initialize FCA analyzer.

        Args:
            fca4j_path: Path to FCA4J JAR file
        """
        self.fca4j_path = fca4j_path
        self.concepts: List[FormalConcept] = []

    def analyze(
        self, context_file: str, output_dir: str = "output/fca"
    ) -> List[FormalConcept]:
        """
        Run FCA analysis on the formal context.

        Args:
            context_file: Path to the formal context CSV file
            output_dir: Directory to save FCA results

        Returns:
            List of extracted formal concepts
        """
        os.makedirs(output_dir, exist_ok=True)

        # Run FCA4J - use XML output format as JSON format has mapping issues
        output_file = os.path.join(output_dir, "concepts.xml")

        try:
            # Execute FCA4J using the lattice command with XML output
            cmd = [
                "java",
                "-jar",
                self.fca4j_path,
                "lattice",
                context_file,
                output_file,
                "-i",
                "CSV",
                "-o",
                "XML",
                "-s",
                "COMMA",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise RuntimeError(f"FCA4J execution failed: {result.stderr}")

            # Parse FCA4J XML output
            self.concepts = self._parse_fca_xml_output(output_file)

        except (FileNotFoundError, RuntimeError) as e:
            # If FCA4J is not available or fails, use a simple fallback implementation
            print(f"FCA4J not available or failed ({e}), using fallback implementation")
            self.concepts = self._fallback_fca_analysis(context_file)

        # Calculate relevance scores
        self._calculate_relevance_scores()

        return self.concepts

    def _parse_fca_xml_output(self, output_file: str) -> List[FormalConcept]:
        """Parse FCA4J XML output.

        FCA4J's XML format correctly maps:
        - <Extent><Object_Ref> = our classes
        - <Intent><Attribute_Ref> = our UML attributes
        """
        import xml.etree.ElementTree as ET

        concepts = []
        concept_map = {}  # ID -> (extent, intent) mapping

        try:
            tree = ET.parse(output_file)
            root = tree.getroot()

            # First pass: collect all concepts with their IDs
            for concept_elem in root.findall("Concept"):
                concept_id = concept_elem.find("ID")
                if concept_id is None or not concept_id.text:
                    continue

                cid = concept_id.text.strip()

                # Extract extent (objects/classes)
                extent = set()
                extent_elem = concept_elem.find("Extent")
                if extent_elem is not None:
                    for obj_ref in extent_elem.findall("Object_Ref"):
                        if obj_ref.text:
                            extent.add(obj_ref.text.strip())

                # Extract intent (attributes)
                intent = set()
                intent_elem = concept_elem.find("Intent")
                if intent_elem is not None:
                    for attr_ref in intent_elem.findall("Attribute_Ref"):
                        if attr_ref.text:
                            intent.add(attr_ref.text.strip())

                # Extract upper covers (parent concepts)
                upper_covers = []
                covers_elem = concept_elem.find("UpperCovers")
                if covers_elem is not None:
                    for cref in covers_elem.findall("Concept_Ref"):
                        if cref.text:
                            upper_covers.append(cref.text.strip())

                concept_map[cid] = {
                    "extent": extent,
                    "intent": intent,
                    "upper_covers": upper_covers,
                }

            # Second pass: infer objects for concepts with empty extent
            # by collecting all objects from descendant concepts
            def get_all_objects(cid, visited=None):
                """Recursively collect all objects from this concept and its descendants."""
                if visited is None:
                    visited = set()
                if cid in visited or cid not in concept_map:
                    return set()
                visited.add(cid)

                objects = concept_map[cid]["extent"].copy()

                # Find all concepts that have this one as upper cover
                for other_id, other_data in concept_map.items():
                    if cid in other_data["upper_covers"]:
                        objects.update(get_all_objects(other_id, visited))

                return objects

            # Third pass: create FormalConcept objects
            for cid, data in concept_map.items():
                extent = data["extent"]
                intent = data["intent"]

                # If extent is empty but intent is not, infer extent from descendants
                if not extent and intent:
                    extent = get_all_objects(cid)

                # Only include concepts with both extent and intent, and extent size >= 2
                if extent and intent and len(extent) >= 2:
                    concepts.append(
                        FormalConcept(
                            extent=extent,
                            intent=intent,
                        )
                    )

        except (FileNotFoundError, ET.ParseError) as e:
            print(f"Error parsing FCA XML output: {e}")
            pass

        return concepts

    def _parse_fca_output(self, output_file: str) -> List[FormalConcept]:
        """Parse FCA4J JSON output (deprecated - use XML instead).

        With CSV format: rows = classes, columns = UML attributes
        - FCA4J's "objects" field = row labels = our classes
        - FCA4J's "attributes" field = column headers = our UML attributes

        This maps correctly to:
        - extent = set of classes (FCA4J "objects")
        - intent = set of UML attributes (FCA4J "attributes")

        Note: JSON format has known issues, XML format is preferred.
        """
        concepts = []

        try:
            with open(output_file, "r") as f:
                data = json.load(f)

            for concept_data in data.get("concepts", []):
                # Direct mapping: objects=classes (extent), attributes=UML attributes (intent)
                extent = set(concept_data.get("objects", []))  # Classes
                intent = set(concept_data.get("attributes", []))  # UML attributes

                # Filter out generic names like "Object 1", "Object 2" that FCA4J generates
                extent = {e for e in extent if not e.startswith("Object ")}
                intent = {i for i in intent if not i.startswith("Object ")}

                # Only include concepts with non-empty extent and intent
                if extent and intent:
                    concepts.append(
                        FormalConcept(
                            extent=extent,
                            intent=intent,
                        )
                    )
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error parsing FCA output: {e}")
            pass

        return concepts

    def _fallback_fca_analysis(self, context_file: str) -> List[FormalConcept]:
        """
        Simple fallback FCA implementation when FCA4J is not available.
        This is a basic implementation for demonstration.
        """
        import csv

        concepts = []

        # Read context
        with open(context_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return concepts

        # Get objects and attributes
        objects = [row["object"] for row in rows]
        attributes = [k for k in rows[0].keys() if k != "object"]

        # Create simple concepts based on common attributes
        # This is simplified - real FCA would compute the concept lattice
        for attr in attributes:
            extent = set()
            for row in rows:
                if (
                    row.get(attr) == "True"
                    or row.get(attr) == "1"
                    or row.get(attr) is True
                ):
                    extent.add(row["object"])

            if extent:
                concepts.append(FormalConcept(extent=extent, intent={attr}))

        return concepts

    def _calculate_relevance_scores(self):
        """Calculate relevance scores for concepts."""
        if not self.concepts:
            return

        max_extent = max(len(c.extent) for c in self.concepts)
        max_intent = max(len(c.intent) for c in self.concepts)

        for concept in self.concepts:
            # Relevance based on extent size and intent size
            # Concepts with moderate size are more relevant
            extent_score = len(concept.extent) / max_extent if max_extent > 0 else 0
            intent_score = len(concept.intent) / max_intent if max_intent > 0 else 0

            # Prefer concepts with multiple objects and multiple attributes
            concept.relevance_score = (extent_score * intent_score) * 100

    def filter_relevant_concepts(
        self, min_relevance: float = 50.0, min_extent_size: int = 2
    ) -> List[FormalConcept]:
        """
        Filter concepts based on relevance criteria.

        Args:
            min_relevance: Minimum relevance score
            min_extent_size: Minimum number of objects in extent

        Returns:
            List of relevant concepts suitable for creating abstract classes
        """
        return [
            c
            for c in self.concepts
            if c.relevance_score >= min_relevance and len(c.extent) >= min_extent_size
        ]

    def export_concepts(self, output_path: str):
        """
        Export concepts to a JSON file for logging and reporting.

        Args:
            output_path: Path to save the concepts
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        concepts_data = [
            {
                "extent": list(c.extent),
                "intent": list(c.intent),
                "relevance_score": c.relevance_score,
            }
            for c in self.concepts
        ]

        with open(output_path, "w") as f:
            json.dump(concepts_data, f, indent=2)
