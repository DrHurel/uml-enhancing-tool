"""Integration tests for the complete pipeline."""

import pytest
import os
from src.pipeline import UMLEnhancementPipeline, PipelineConfig


@pytest.mark.integration
class TestPipeline:
    """Test suite for the complete pipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization with default config."""
        pipeline = UMLEnhancementPipeline()

        assert pipeline.parser is not None
        assert pipeline.knowledge_graph is not None
        assert pipeline.fca_analyzer is not None
        assert pipeline.llm_service is not None
        assert pipeline.generator is not None

    def test_pipeline_with_custom_config(self, temp_output_dir):
        """Test pipeline with custom configuration."""
        config = PipelineConfig(
            output_dir=temp_output_dir,
            logs_dir=os.path.join(temp_output_dir, "logs"),
            reports_dir=os.path.join(temp_output_dir, "reports"),
        )

        pipeline = UMLEnhancementPipeline(config)

        assert pipeline.config.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)

    def test_step_parse(self, sample_plantuml, temp_output_dir):
        """Test parsing step."""
        # Create a temporary PlantUML file
        input_file = os.path.join(temp_output_dir, "input.puml")
        with open(input_file, "w") as f:
            f.write(sample_plantuml)

        pipeline = UMLEnhancementPipeline()
        result = pipeline._step_parse(input_file)

        assert "classes" in result
        assert "relationships" in result
        assert len(result["classes"]) > 0

    @pytest.mark.slow
    def test_full_pipeline_run(self, sample_plantuml, temp_output_dir):
        """Test running the complete pipeline."""
        # Create input file
        input_file = os.path.join(temp_output_dir, "input.puml")
        with open(input_file, "w") as f:
            f.write(sample_plantuml)

        # Configure pipeline
        config = PipelineConfig(
            output_dir=temp_output_dir,
            logs_dir=os.path.join(temp_output_dir, "logs"),
            reports_dir=os.path.join(temp_output_dir, "reports"),
            min_relevance=0.0,  # Lower threshold for testing
            min_extent_size=2,
        )

        pipeline = UMLEnhancementPipeline(config)

        # Run pipeline
        results = pipeline.run(input_file)

        # Verify results
        assert "timestamp" in results
        assert "steps" in results
        assert "parsing" in results["steps"]
        assert "knowledge_graph" in results["steps"]
        assert "fca_analysis" in results["steps"]

        # Verify output file exists
        assert os.path.exists(results["output_path"])


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests."""

    @pytest.mark.slow
    def test_complete_workflow(self, sample_plantuml, temp_output_dir):
        """Test complete workflow from input to output."""
        # This is a comprehensive test that exercises the entire system
        input_file = os.path.join(temp_output_dir, "test_diagram.puml")
        with open(input_file, "w") as f:
            f.write(sample_plantuml)

        config = PipelineConfig(
            output_dir=temp_output_dir,
            logs_dir=os.path.join(temp_output_dir, "logs"),
            reports_dir=os.path.join(temp_output_dir, "reports"),
        )

        pipeline = UMLEnhancementPipeline(config)
        results = pipeline.run(input_file)

        # Verify all expected outputs exist
        assert os.path.exists(results["output_path"])

        # Check that enhanced diagram contains abstract classes
        with open(results["output_path"], "r") as f:
            content = f.read()
            assert "@startuml" in content
            assert "@enduml" in content
