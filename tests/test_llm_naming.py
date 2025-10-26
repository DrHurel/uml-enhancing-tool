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

    def test_initialization_with_anthropic(self):
        """Test LLM service initialization with Anthropic provider."""
        # Test that anthropic provider is accepted (initialization happens lazily)
        service = LLMNamingService(provider="anthropic", api_key="fake-key")
        assert service.provider == "anthropic"
        assert service.api_key == "fake-key"

    def test_initialization_missing_openai(self, monkeypatch):
        """Test initialization fails gracefully when OpenAI not installed."""
        service = LLMNamingService(provider="openai", api_key="test-key")

        # Simulate ImportError for openai
        def mock_import_error(*args, **kwargs):
            raise ImportError("No module named 'openai'")

        import builtins

        real_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("No module named 'openai'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", custom_import)

        with pytest.raises(ImportError, match="OpenAI package not installed"):
            service._initialize_client()

    def test_initialization_missing_anthropic(self, monkeypatch):
        """Test initialization fails gracefully when Anthropic not installed."""
        service = LLMNamingService(provider="anthropic", api_key="test-key")

        # Simulate ImportError for anthropic
        import builtins

        real_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == "anthropic":
                raise ImportError("No module named 'anthropic'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", custom_import)

        with pytest.raises(ImportError, match="Anthropic package not installed"):
            service._initialize_client()

    def test_fallback_naming_patterns(self):
        """Test various fallback naming patterns."""
        service = LLMNamingService()

        # Test with user-related intent
        ac1 = AbstractClass(
            extent=["UserManager", "AdminUser"], intent=["+login()", "+authenticate()"]
        )
        result1 = service._fallback_naming(ac1)
        assert "User" in result1.suggested_name or "Auth" in result1.suggested_name

        # Test with identifiable pattern
        ac2 = AbstractClass(extent=["Product", "Order"], intent=["+getId()"])
        result2 = service._fallback_naming(ac2)
        assert result2.suggested_name is not None

    def test_abstract_class_with_relevance_score(self):
        """Test AbstractClass with relevance_score field."""
        ac = AbstractClass(
            extent=["A", "B"],
            intent=["m1()"],
            suggested_name="Test",
            confidence=0.8,
            relevance_score=75.0,
        )

        assert ac.relevance_score == 75.0
        assert ac.confidence == 0.8
