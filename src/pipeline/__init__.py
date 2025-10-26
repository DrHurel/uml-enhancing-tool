"""Pipeline orchestration module for the UML enhancement process."""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from ..parser import PlantUMLParser
from ..knowledge_graph import KnowledgeGraph
from ..fca_analyzer import FCAAnalyzer
from ..llm_naming import LLMNamingService, AbstractClass
from ..generator import PlantUMLGenerator
from ..evaluator import ConceptEvaluator


class PipelineConfig:
    """Configuration for the pipeline."""

    def __init__(
        self,
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        fca4j_path: str = "fca4j-cli-0.4.4.jar",
        min_relevance: float = 50.0,
        min_extent_size: int = 2,
        output_dir: str = "output",
        logs_dir: str = "logs",
        reports_dir: str = "reports",
    ):
        """Initialize pipeline configuration."""
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.fca4j_path = fca4j_path
        self.min_relevance = min_relevance
        self.min_extent_size = min_extent_size
        self.output_dir = output_dir
        self.logs_dir = logs_dir
        self.reports_dir = reports_dir


class UMLEnhancementPipeline:
    """Main pipeline for UML diagram enhancement."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        self._setup_logging()

        # Initialize components
        self.parser = PlantUMLParser()
        self.knowledge_graph = KnowledgeGraph()
        self.fca_analyzer = FCAAnalyzer(fca4j_path=self.config.fca4j_path)
        self.llm_service = LLMNamingService(
            provider=self.config.llm_provider, api_key=self.config.llm_api_key
        )
        self.generator = PlantUMLGenerator()
        self.evaluator = ConceptEvaluator()

        # Create output directories
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.logs_dir, exist_ok=True)
        os.makedirs(self.config.reports_dir, exist_ok=True)

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = os.path.join(
            self.config.logs_dir,
            f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )

        os.makedirs(self.config.logs_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        self.logger = logging.getLogger(__name__)

    def run(self, input_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Run the complete enhancement pipeline.

        Args:
            input_path: Path to input PlantUML file
            output_path: Path for output enhanced diagram (optional)

        Returns:
            Dictionary containing pipeline results and statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting UML Enhancement Pipeline")
        self.logger.info("=" * 80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_path is None:
            input_name = Path(input_path).stem
            output_path = os.path.join(
                self.config.output_dir, f"{input_name}_enhanced_{timestamp}.puml"
            )

        results = {
            "timestamp": timestamp,
            "input_path": input_path,
            "output_path": output_path,
            "steps": {},
        }

        # Step 1: Parse PlantUML
        self.logger.info("Step 1: Parsing PlantUML diagram...")
        parsed_data = self._step_parse(input_path)
        results["steps"]["parsing"] = {
            "classes_count": len(parsed_data["classes"]),
            "relationships_count": len(parsed_data["relationships"]),
        }
        self.logger.info(f"  - Parsed {len(parsed_data['classes'])} classes")
        self.logger.info(
            f"  - Parsed {len(parsed_data['relationships'])} relationships"
        )

        # Step 2: Build Knowledge Graph
        self.logger.info("Step 2: Building knowledge graph...")
        kg = self._step_build_knowledge_graph(parsed_data)
        kg_output = os.path.join(
            self.config.output_dir, f"knowledge_graph_{timestamp}.json"
        )
        self._export_knowledge_graph(kg, kg_output)
        results["steps"]["knowledge_graph"] = {
            "nodes_count": kg.number_of_nodes(),
            "edges_count": kg.number_of_edges(),
            "output_file": kg_output,
        }
        self.logger.info(f"  - Created graph with {kg.number_of_nodes()} nodes")
        self.logger.info(f"  - Saved to {kg_output}")

        # Step 3: Export for FCA
        self.logger.info("Step 3: Exporting formal context for FCA...")
        fca_context = os.path.join(
            self.config.output_dir, f"fca_context_{timestamp}.csv"
        )
        self.knowledge_graph.export_for_fca(fca_context)
        results["steps"]["fca_export"] = {"context_file": fca_context}
        self.logger.info(f"  - Exported to {fca_context}")

        # Step 4: FCA Analysis
        self.logger.info("Step 4: Running FCA analysis...")
        concepts = self._step_fca_analysis(fca_context, timestamp)
        concepts_output = os.path.join(
            self.config.reports_dir, f"concepts_{timestamp}.json"
        )
        self.fca_analyzer.export_concepts(concepts_output)
        results["steps"]["fca_analysis"] = {
            "total_concepts": len(concepts),
            "relevant_concepts": len(
                self.fca_analyzer.filter_relevant_concepts(
                    self.config.min_relevance, self.config.min_extent_size
                )
            ),
            "output_file": concepts_output,
        }
        self.logger.info(f"  - Extracted {len(concepts)} formal concepts")
        self.logger.info(f"  - Saved to {concepts_output}")

        # Step 5: Filter Relevant Concepts
        self.logger.info("Step 5: Filtering relevant concepts...")
        relevant_concepts = self.fca_analyzer.filter_relevant_concepts(
            self.config.min_relevance, self.config.min_extent_size
        )
        self.logger.info(
            f"  - Found {len(relevant_concepts)} relevant concepts for abstraction"
        )

        # Step 6: Create Abstract Classes
        self.logger.info("Step 6: Creating abstract classes...")
        abstract_classes = self._step_create_abstract_classes(relevant_concepts)

        # Expand abstract classes to include subsumed classes (e.g., Truck for Vehicle)
        abstract_classes = self._expand_abstract_class_extents(
            abstract_classes, parsed_data["classes"]
        )

        self.logger.info(f"  - Created {len(abstract_classes)} abstract classes")

        # Step 7: Name Abstract Classes with LLM
        self.logger.info("Step 7: Naming abstract classes using LLM...")
        named_classes = self._step_name_abstract_classes(abstract_classes)
        abstract_output = os.path.join(
            self.config.reports_dir, f"abstract_classes_{timestamp}.json"
        )
        self.llm_service.export_named_classes(named_classes, abstract_output)
        results["steps"]["abstract_classes"] = {
            "count": len(named_classes),
            "output_file": abstract_output,
        }
        for ac in named_classes:
            self.logger.info(f"  - {ac.suggested_name}: {', '.join(ac.extent)}")

        # Step 8: Generate Enhanced Diagram
        self.logger.info("Step 8: Generating enhanced PlantUML diagram...")
        self._step_generate_diagram(
            parsed_data["classes"],
            parsed_data["relationships"],
            named_classes,
            output_path,
        )
        results["steps"]["generation"] = {"output_file": output_path}
        self.logger.info(f"  - Saved enhanced diagram to {output_path}")

        # Step 9: Evaluate Concepts
        self.logger.info("Step 9: Evaluating abstract class concepts...")
        self._step_evaluate_concepts(named_classes, relevant_concepts, timestamp)
        evaluation_csv = os.path.join(
            self.config.reports_dir, f"evaluation_{timestamp}.csv"
        )
        evaluation_simple = os.path.join(
            self.config.reports_dir, f"evaluation_simple_{timestamp}.csv"
        )
        self.evaluator.export_evaluation_csv(evaluation_csv, include_template=True)
        self.evaluator.export_simple_csv(evaluation_simple)
        results["steps"]["evaluation"] = {
            "evaluation_csv": evaluation_csv,
            "evaluation_simple_csv": evaluation_simple,
            "concepts_evaluated": len(named_classes),
        }
        self.logger.info(f"  - Saved evaluation template to {evaluation_csv}")
        self.logger.info(f"  - Saved simple evaluation to {evaluation_simple}")

        # Step 10: Generate Report
        self.logger.info("Step 10: Generating comparison report...")
        report_path = os.path.join(self.config.reports_dir, f"report_{timestamp}.md")
        self.generator.generate_comparison_report(input_path, output_path, report_path)
        results["steps"]["report"] = {"output_file": report_path}
        self.logger.info(f"  - Saved report to {report_path}")

        # Save pipeline results
        results_path = os.path.join(
            self.config.reports_dir, f"results_{timestamp}.json"
        )
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info("=" * 80)
        self.logger.info("Pipeline completed successfully!")
        self.logger.info(f"Results saved to {results_path}")
        self.logger.info("=" * 80)

        return results

    def _step_parse(self, input_path: str) -> Dict:
        """Step 1: Parse PlantUML diagram."""
        with open(input_path, "r") as f:
            content = f.read()
        return self.parser.parse(content)

    def _step_build_knowledge_graph(self, parsed_data: Dict):
        """Step 2: Build knowledge graph."""
        return self.knowledge_graph.from_uml_model(
            parsed_data["classes"], parsed_data["relationships"]
        )

    def _export_knowledge_graph(self, kg, output_path: str):
        """Export knowledge graph to JSON."""
        import networkx as nx
        from networkx.readwrite import json_graph

        data = json_graph.node_link_data(kg)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def _step_fca_analysis(self, context_file: str, timestamp: str):
        """Step 4: Run FCA analysis."""
        output_dir = os.path.join(self.config.output_dir, f"fca_{timestamp}")
        return self.fca_analyzer.analyze(context_file, output_dir)

    def _step_create_abstract_classes(self, concepts) -> list:
        """Step 6: Create abstract classes from concepts."""
        abstract_classes = []
        for concept in concepts:
            abstract_classes.append(
                AbstractClass(extent=list(concept.extent), intent=list(concept.intent))
            )
        return abstract_classes

    def _expand_abstract_class_extents(self, abstract_classes, all_classes):
        """
        Expand abstract classes to include subsumed classes.
        If a class has ALL attributes/methods of an abstract class (plus possibly more),
        it should inherit from that abstract class.
        """
        for abstract_class in abstract_classes:
            abstract_intent = set(abstract_class.intent)
            current_extent = set(abstract_class.extent)

            # Check all classes
            for class_name, uml_class in all_classes.items():
                if class_name in current_extent:
                    continue  # Already in extent

                # Get all features of this class
                class_features = set()
                for attr in uml_class.attributes:
                    class_features.add(attr)
                for method in uml_class.methods:
                    class_features.add(method)

                # If class has ALL features of the abstract class, add it to extent
                if abstract_intent.issubset(class_features):
                    abstract_class.extent.append(class_name)

        return abstract_classes

    def _step_name_abstract_classes(self, abstract_classes):
        """Step 7: Name abstract classes."""
        return self.llm_service.batch_name_abstract_classes(abstract_classes)

    def _step_generate_diagram(
        self, classes, relationships, abstract_classes, output_path
    ):
        """Step 8: Generate enhanced diagram."""
        return self.generator.generate(
            classes, relationships, abstract_classes, output_path
        )

    def _step_evaluate_concepts(self, named_classes, fca_concepts, timestamp):
        """Step 9: Evaluate abstract class concepts and generate metrics."""
        # Create a mapping of extent to FCA concept for evaluation
        concept_map = {}
        for concept in fca_concepts:
            key = frozenset(concept.extent)
            concept_map[key] = concept

        # Evaluate each abstract class
        for idx, abstract_class in enumerate(named_classes, start=1):
            concept_id = f"C_{timestamp}_{idx}"

            # Find matching FCA concept
            extent_key = frozenset(abstract_class.extent)
            fca_concept = concept_map.get(extent_key)

            # Generate evaluation
            self.evaluator.evaluate_concept(abstract_class, concept_id, fca_concept)
