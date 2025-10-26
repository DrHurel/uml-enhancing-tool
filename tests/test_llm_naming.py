"""Unit tests for LLM naming service."""

import pytest
from src.llm_naming import LLMNamingService, AbstractClass


@pytest.mark.unit
class TestLLMNamingService:
    """Test suite for LLM naming service."""

    def test_initialization(self):
        """Test LLM service initialization."""
        service = LLMNamingService(provider="openai")
        assert service.provider == "openai"

    def test_abstract_class_dataclass(self):
        """Test AbstractClass dataclass."""
        ac = AbstractClass(
            extent=["Dog", "Cat"], intent=["name", "age"], suggested_name="Animal"
        )

        assert len(ac.extent) == 2
        assert len(ac.intent) == 2
        assert ac.suggested_name == "Animal"

    def test_fallback_naming(self):
        """Test fallback naming strategy."""
        service = LLMNamingService()

        ac = AbstractClass(extent=["Dog", "Cat"], intent=["name", "age"])

        result = service._fallback_naming(ac)

        assert result.suggested_name is not None
        assert len(result.suggested_name) > 0
        assert result.confidence == 0.5

    def test_create_naming_prompt(self):
        """Test creating naming prompt."""
        service = LLMNamingService()

        ac = AbstractClass(extent=["Dog", "Cat"], intent=["name", "age", "eat()"])

        prompt = service._create_naming_prompt(ac)

        assert "Dog" in prompt
        assert "Cat" in prompt
        assert "name" in prompt
        assert "PascalCase" in prompt

    def test_parse_llm_response(self):
        """Test parsing LLM response."""
        service = LLMNamingService()

        # Test clean response
        assert service._parse_llm_response("Animal") == "Animal"

        # Test response with quotes
        assert service._parse_llm_response('"Animal"') == "Animal"

        # Test response with explanation (take first line)
        assert service._parse_llm_response("Animal\nThis is a good name") == "Animal"

        # Test lowercase response
        result = service._parse_llm_response("animal")
        assert result[0].isupper()

    def test_batch_name_abstract_classes(self):
        """Test batch naming."""
        service = LLMNamingService()

        abstract_classes = [
            AbstractClass(extent=["Dog", "Cat"], intent=["name"]),
            AbstractClass(extent=["Car", "Truck"], intent=["speed"]),
        ]

        result = service.batch_name_abstract_classes(abstract_classes)

        assert len(result) == 2
        assert all(ac.suggested_name is not None for ac in result)

    def test_export_named_classes(self, temp_output_dir):
        """Test exporting named classes."""
        import os
        import json

        service = LLMNamingService()

        abstract_classes = [
            AbstractClass(
                extent=["Dog", "Cat"],
                intent=["name"],
                suggested_name="Animal",
                confidence=0.9,
            )
        ]

        output_path = os.path.join(temp_output_dir, "named_classes.json")
        service.export_named_classes(abstract_classes, output_path)

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["name"] == "Animal"
