"""Evaluation module for tracking and exporting abstract class quality metrics."""

import os
import csv
from typing import List, Dict
from dataclasses import dataclass, asdict


@dataclass
class ConceptEvaluation:
    """Represents evaluation data for a generated abstract class concept."""

    # LLM Answer fields
    id_concept: str
    concept_name: str
    name_justification: str
    name_relevance_score: float  # NRS in [0..1]
    justification_nrs: str
    abstraction_relevance_score: float  # ARS in [0..1]
    justification_ars: str

    # Derived from FCA analysis
    extent: List[str]  # Classes that inherit
    intent: List[str]  # Common attributes/methods
    relevance_score: float  # From FCA analysis
    confidence: float  # From LLM naming

    def to_evaluation_row(self) -> Dict:
        """Convert to CSV row format for evaluation."""
        return {
            "Id Concept": self.id_concept,
            "Concept name": self.concept_name,
            "Name justification": self.name_justification,
            "Name relevance score (NRS)": self.name_relevance_score,
            "Justification for the NRS score": self.justification_nrs,
            "Abstraction relevance score (ARS)": self.abstraction_relevance_score,
            "justification for the ARS score": self.justification_ars,
            # Additional metadata
            "Extent (child classes)": ", ".join(self.extent),
            "Intent (common features)": ", ".join(self.intent),
            "FCA Relevance Score": self.relevance_score,
            "LLM Confidence": self.confidence,
        }


class ConceptEvaluator:
    """Service for evaluating and exporting abstract class concepts."""

    def __init__(self):
        self.evaluations: List[ConceptEvaluation] = []

    def evaluate_concept(
        self, abstract_class, concept_id: str, fca_concept=None
    ) -> ConceptEvaluation:
        """
        Create evaluation data for an abstract class.

        Args:
            abstract_class: The named abstract class
            concept_id: Unique identifier for this concept
            fca_concept: Original FCA concept (optional)

        Returns:
            ConceptEvaluation object
        """
        # Generate name justification from common features
        name_justification = self._generate_name_justification(abstract_class)

        # Calculate name relevance score (NRS)
        # Based on how well the name reflects the common attributes
        nrs = self._calculate_name_relevance_score(abstract_class)
        justification_nrs = self._generate_nrs_justification(abstract_class, nrs)

        # Calculate abstraction relevance score (ARS)
        # Based on the usefulness of extracting this abstraction
        ars = self._calculate_abstraction_relevance_score(abstract_class, fca_concept)
        justification_ars = self._generate_ars_justification(
            abstract_class, fca_concept, ars
        )

        evaluation = ConceptEvaluation(
            id_concept=concept_id,
            concept_name=abstract_class.suggested_name,
            name_justification=name_justification,
            name_relevance_score=nrs,
            justification_nrs=justification_nrs,
            abstraction_relevance_score=ars,
            justification_ars=justification_ars,
            extent=abstract_class.extent,
            intent=abstract_class.intent,
            relevance_score=fca_concept.relevance_score if fca_concept else 0.0,
            confidence=abstract_class.confidence,
        )

        self.evaluations.append(evaluation)
        return evaluation

    def _generate_name_justification(self, abstract_class) -> str:
        """Generate justification for the chosen name."""
        # Extract attribute/method names from intent
        attributes = [
            f for f in abstract_class.intent if ":" in f or not f.endswith(")")
        ]
        methods = [f for f in abstract_class.intent if f.endswith(")")]

        justification_parts = []

        if attributes:
            attr_names = ", ".join([a.split(":")[0].strip() for a in attributes[:3]])
            justification_parts.append(f"Common attributes: {attr_names}")

        if methods:
            method_names = ", ".join([m.replace("()", "").strip() for m in methods[:3]])
            justification_parts.append(f"Common methods: {method_names}")

        if len(abstract_class.extent) > 0:
            justification_parts.append(
                f"Shared by {len(abstract_class.extent)} classes: {', '.join(abstract_class.extent[:3])}"
            )

        return ". ".join(justification_parts) + "."

    def _calculate_name_relevance_score(self, abstract_class) -> float:
        """
        Calculate how relevant the name is (NRS).
        Score in [0..1] based on:
        - Confidence from LLM
        - Whether name reflects common features
        - Name length and clarity
        """
        score = abstract_class.confidence

        # Adjust based on name quality
        name = abstract_class.suggested_name

        # Penalize very generic names
        if name.startswith("Abstract") and len(name) < 15:
            score *= 0.8

        # Reward descriptive names
        if len(name) > 8 and not name.startswith("Abstract"):
            score = min(1.0, score * 1.1)

        return round(score, 2)

    def _generate_nrs_justification(self, abstract_class, nrs: float) -> str:
        """Generate justification for the NRS score."""
        name = abstract_class.suggested_name

        if nrs >= 0.8:
            return f"Name '{name}' clearly describes the common concept and is semantically appropriate."
        elif nrs >= 0.6:
            return f"Name '{name}' is adequate but could be more descriptive of the common features."
        elif nrs >= 0.4:
            return f"Name '{name}' is generic; derived from common attribute but not strongly semantic."
        else:
            return f"Name '{name}' is a fallback naming; low semantic meaning."

    def _calculate_abstraction_relevance_score(
        self, abstract_class, fca_concept
    ) -> float:
        """
        Calculate abstraction relevance score (ARS).
        Score in [0..1] based on:
        - Number of child classes (extent size)
        - Number of common features (intent size)
        - FCA relevance score
        """
        extent_size = len(abstract_class.extent)
        intent_size = len(abstract_class.intent)

        # Base score from FCA relevance (already 0-100, normalize to 0-1)
        fca_score = (
            (fca_concept.relevance_score / 100.0) if fca_concept else extent_size / 10
        )

        # Factor in the value of extraction
        # More child classes and more common features = higher value
        value_score = min(1.0, (extent_size / 5.0 + intent_size / 10.0) / 2)

        # Weighted combination
        ars = (fca_score * 0.6) + (value_score * 0.4)

        return round(min(1.0, ars), 2)

    def _generate_ars_justification(
        self, abstract_class, fca_concept, ars: float
    ) -> str:
        """Generate justification for the ARS score."""
        extent_size = len(abstract_class.extent)
        intent_size = len(abstract_class.intent)

        if ars >= 0.8:
            return f"Highly valuable abstraction: {extent_size} classes share {intent_size} features. Significant code reuse opportunity."
        elif ars >= 0.6:
            return f"Useful abstraction: {extent_size} classes with {intent_size} common features. Good for code organization."
        elif ars >= 0.4:
            return f"Moderate value: {extent_size} classes share {intent_size} features. Limited reuse benefit."
        else:
            return f"Low value: Only {extent_size} classes with {intent_size} common features. Questionable abstraction."

    def export_evaluation_csv(self, output_path: str, include_template: bool = True):
        """
        Export evaluations to CSV file in the specified format.

        Args:
            output_path: Path to save the CSV file
            include_template: If True, include header rows with evaluation template
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")

            if include_template:
                # Write header rows as per template
                writer.writerow(
                    [
                        "Evaluation of the result",
                        "",
                        "Answer of the LLM",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "Your evaluation",
                        "and your comments",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]
                )

                writer.writerow(
                    [
                        " ",
                        "Id Concept",
                        "Concept name",
                        "Name justification",
                        "Name relevance score (NRS)",
                        "Justification for the NRS score",
                        "Abstraction relevance score (ARS)",
                        "justification for the ARS score",
                        "Concept name",
                        "",
                        "Other concept name you imagine",
                        "",
                        "Name justification",
                        "",
                        "Name relevance score (NRS)",
                        "",
                        "justification for the NRS score",
                        "",
                        "Abstraction relevance score (ARS)",
                        "",
                        "Justification for the ARS score",
                        "",
                        "Other comments",
                    ]
                )

                writer.writerow(
                    [
                        "output type",
                        "string",
                        "string",
                        "string",
                        "In [0..1]",
                        "string",
                        "In [0..1]",
                        "string",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment Concept name",
                        "string",
                        "comment Other concept name",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment Name Justification (especially for 1 and 2)",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment NRS (especially for 1 and 2)",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment Justification NRS (especially for 1 and 2)",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment ARS (especially for 1 and 2)",
                        "agree (2), do not agree (0), perhaps (1)",
                        "comment Justification ARS (especially for 1 and 2)",
                        "string",
                    ]
                )

            # Write data rows
            for idx, evaluation in enumerate(self.evaluations, start=1):
                # Format extent and intent
                extent_str = ", ".join(evaluation.extent)
                intent_str = ", ".join(evaluation.intent[:3])  # First 3 features

                writer.writerow(
                    [
                        f"Run_{evaluation.id_concept}",  # Row identifier
                        evaluation.id_concept,
                        evaluation.concept_name,
                        evaluation.name_justification,
                        evaluation.name_relevance_score,
                        evaluation.justification_nrs,
                        evaluation.abstraction_relevance_score,
                        evaluation.justification_ars,
                        "",  # Your evaluation: Concept name (empty for user)
                        "",  # comment
                        "",  # Other concept name you imagine (empty for user)
                        "",  # comment
                        "",  # agree/disagree Name justification (empty for user)
                        "",  # comment
                        "",  # agree/disagree NRS (empty for user)
                        "",  # comment
                        "",  # agree/disagree Justification NRS (empty for user)
                        "",  # comment
                        "",  # agree/disagree ARS (empty for user)
                        "",  # comment
                        "",  # agree/disagree Justification ARS (empty for user)
                        "",  # comment
                        f"Extent: {extent_str}. Intent: {intent_str}",  # Other comments
                    ]
                )

    def export_simple_csv(self, output_path: str):
        """
        Export a simpler CSV format with just the key metrics.

        Args:
            output_path: Path to save the CSV file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "Id Concept",
                "Concept name",
                "Name justification",
                "Name relevance score (NRS)",
                "Justification for the NRS score",
                "Abstraction relevance score (ARS)",
                "justification for the ARS score",
                "Extent (child classes)",
                "Intent (common features)",
                "FCA Relevance Score",
                "LLM Confidence",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for evaluation in self.evaluations:
                writer.writerow(evaluation.to_evaluation_row())
