"""LLM naming module for generating meaningful names for abstract classes."""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class AbstractClass:
    """Represents an abstract class to be named."""

    extent: List[str]  # Classes that will inherit from this abstract class
    intent: List[str]  # Common attributes/features
    suggested_name: Optional[str] = None
    confidence: float = 0.0


class LLMNamingService:
    """Service for naming abstract classes using LLM."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Initialize LLM naming service.

        Args:
            provider: LLM provider ('openai' or 'anthropic')
            api_key: API key for the LLM service
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.client = None

        if self.api_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client."""
        if self.provider == "openai":
            try:
                import openai

                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Run: pip install openai"
                )
        elif self.provider == "anthropic":
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. Run: pip install anthropic"
                )

    def name_abstract_class(self, abstract_class: AbstractClass) -> AbstractClass:
        """
        Generate a meaningful name for an abstract class using LLM.

        Args:
            abstract_class: The abstract class to name

        Returns:
            AbstractClass with suggested_name filled in
        """
        if not self.client:
            # Fallback to simple naming strategy
            return self._fallback_naming(abstract_class)

        prompt = self._create_naming_prompt(abstract_class)

        try:
            if self.provider == "openai":
                response = self._query_openai(prompt)
            elif self.provider == "anthropic":
                response = self._query_anthropic(prompt)
            else:
                return self._fallback_naming(abstract_class)

            # Parse response
            abstract_class.suggested_name = self._parse_llm_response(response)
            abstract_class.confidence = 0.9  # High confidence for LLM-generated names

        except Exception as e:
            print(f"LLM naming failed: {e}. Using fallback naming.")
            return self._fallback_naming(abstract_class)

        return abstract_class

    def _create_naming_prompt(self, abstract_class: AbstractClass) -> str:
        """Create a prompt for the LLM to name the abstract class."""
        prompt = f"""You are a software architecture expert. Based on the following information about a group of related classes, suggest a concise and meaningful name for an abstract class that would represent their common concept.

Classes that will inherit from this abstract class:
{", ".join(abstract_class.extent)}

Common attributes and features:
{", ".join(abstract_class.intent)}

Provide ONLY the suggested abstract class name (in PascalCase), without any explanation or additional text. The name should be:
- Concise (1-3 words)
- Descriptive of the common concept
- Follow UML/OOP naming conventions
- Not include the word "Abstract" unless necessary

Suggested name:"""

        return prompt

    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI API."""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a software architecture expert specializing in object-oriented design.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=50,
        )
        return response.choices[0].message.content.strip()

    def _query_anthropic(self, prompt: str) -> str:
        """Query Anthropic API."""
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def _parse_llm_response(self, response: str) -> str:
        """Parse and clean the LLM response."""
        # Remove any quotes, extra whitespace, or explanations
        name = response.strip().strip('"').strip("'")

        # Take only the first line if multiple lines returned
        if "\n" in name:
            name = name.split("\n")[0]

        # Sanitize the name to ensure valid PlantUML syntax
        name = self._sanitize_class_name(name)

        return name

    def _sanitize_class_name(self, name: str) -> str:
        """
        Sanitize a string to be a valid PlantUML class name.
        Removes special characters and converts to PascalCase.
        """
        # Remove visibility modifiers (+, -, #, ~)
        name = name.lstrip("+-#~")

        # Extract just the attribute name (before : type declaration)
        if ":" in name:
            name = name.split(":")[0].strip()

        # Remove parentheses and other special chars
        name = "".join(c for c in name if c.isalnum() or c in ("_", " "))

        # Convert to PascalCase
        name = name.replace("_", " ").title().replace(" ", "")

        return name

    def _fallback_naming(self, abstract_class: AbstractClass) -> AbstractClass:
        """
        Fallback naming strategy when LLM is not available.
        Creates a simple name based on common attributes.
        """
        if abstract_class.intent:
            # Use the first common attribute as base for the name
            base_name = self._sanitize_class_name(abstract_class.intent[0])
            abstract_class.suggested_name = f"Abstract{base_name}"
        else:
            # Use extent as base
            if len(abstract_class.extent) > 0:
                base_name = abstract_class.extent[0]
                abstract_class.suggested_name = f"Abstract{base_name}"
            else:
                abstract_class.suggested_name = "AbstractBase"

        abstract_class.confidence = 0.5  # Lower confidence for fallback naming

        return abstract_class

    def batch_name_abstract_classes(
        self, abstract_classes: List[AbstractClass]
    ) -> List[AbstractClass]:
        """
        Name multiple abstract classes.

        Args:
            abstract_classes: List of abstract classes to name

        Returns:
            List of abstract classes with suggested names
        """
        named_classes = []

        for abstract_class in abstract_classes:
            named_class = self.name_abstract_class(abstract_class)
            named_classes.append(named_class)

        return named_classes

    def export_named_classes(
        self, abstract_classes: List[AbstractClass], output_path: str
    ):
        """
        Export named abstract classes to a JSON file.

        Args:
            abstract_classes: List of named abstract classes
            output_path: Path to save the data
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        data = [
            {
                "name": ac.suggested_name,
                "extent": ac.extent,
                "intent": ac.intent,
                "confidence": ac.confidence,
            }
            for ac in abstract_classes
        ]

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
