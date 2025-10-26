#!/usr/bin/env python3
"""
UML Enhancing Tool - Main CLI Entry Point

A tool that implements a pipeline to enhance UML diagrams using FCA & AI techniques.
"""

import click
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.pipeline import UMLEnhancementPipeline, PipelineConfig


# Load environment variables
load_dotenv()


@click.command()
@click.option(
    "--input",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Path to input PlantUML diagram file (.puml)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Path for output enhanced diagram (default: input_enhanced_timestamp.puml)",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="output",
    help="Directory for output files (default: output/)",
)
@click.option(
    "--logs-dir",
    type=click.Path(),
    default="logs",
    help="Directory for log files (default: logs/)",
)
@click.option(
    "--reports-dir",
    type=click.Path(),
    default="reports",
    help="Directory for report files (default: reports/)",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["openai", "anthropic"], case_sensitive=False),
    default="openai",
    help="LLM provider for naming abstract classes (default: openai)",
)
@click.option(
    "--llm-api-key",
    type=str,
    help="API key for LLM provider (or set via environment variable)",
)
@click.option(
    "--fca4j-path",
    type=click.Path(exists=True),
    default="fca4j-cli-0.4.4.jar",
    help="Path to FCA4J JAR file (default: fca4j-cli-0.4.4.jar)",
)
@click.option(
    "--min-relevance",
    type=float,
    default=50.0,
    help="Minimum relevance score for concepts (default: 50.0)",
)
@click.option(
    "--min-extent-size",
    type=int,
    default=2,
    help="Minimum extent size for concepts (default: 2)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(
    input,
    output,
    output_dir,
    logs_dir,
    reports_dir,
    llm_provider,
    llm_api_key,
    fca4j_path,
    min_relevance,
    min_extent_size,
    verbose,
):
    """
    UML Enhancing Tool - Enhance UML diagrams using FCA & AI techniques.

    This tool processes PlantUML diagrams and enhances them by:

    \b
    1. Parsing the input diagram
    2. Building a knowledge graph
    3. Extracting formal concepts using FCA
    4. Creating abstract classes from relevant concepts
    5. Naming abstract classes using LLM
    6. Generating an enhanced PlantUML diagram

    Example:

        python main.py --input diagram.puml --output enhanced.puml
    """

    # Display banner
    if verbose:
        click.echo("=" * 80)
        click.echo("UML Enhancing Tool")
        click.echo("A pipeline to enhance UML diagrams using FCA & AI techniques")
        click.echo("=" * 80)
        click.echo()

    # Validate input file
    if not input.endswith(".puml") and not input.endswith(".plantuml"):
        click.secho("Warning: Input file doesn't have .puml extension", fg="yellow")

    # Configure pipeline
    config = PipelineConfig(
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        fca4j_path=fca4j_path,
        min_relevance=min_relevance,
        min_extent_size=min_extent_size,
        output_dir=output_dir,
        logs_dir=logs_dir,
        reports_dir=reports_dir,
    )

    try:
        # Initialize pipeline
        if verbose:
            click.echo("Initializing pipeline...")

        pipeline = UMLEnhancementPipeline(config)

        # Run pipeline
        click.echo(f"Processing: {input}")
        results = pipeline.run(input, output)

        # Display results
        click.echo()
        click.secho("✓ Pipeline completed successfully!", fg="green", bold=True)
        click.echo()
        click.echo(f"Enhanced diagram: {results['output_path']}")
        click.echo(f"Reports directory: {reports_dir}/")
        click.echo(f"Logs directory: {logs_dir}/")

        if verbose:
            click.echo()
            click.echo("Pipeline Statistics:")
            click.echo(
                f"  - Classes parsed: {results['steps']['parsing']['classes_count']}"
            )
            click.echo(
                f"  - Relationships parsed: {results['steps']['parsing']['relationships_count']}"
            )
            click.echo(
                f"  - Formal concepts: {results['steps']['fca_analysis']['total_concepts']}"
            )
            click.echo(
                f"  - Abstract classes created: {results['steps']['abstract_classes']['count']}"
            )

        click.echo()
        click.secho("View the enhanced diagram and reports for details!", fg="cyan")

    except FileNotFoundError as e:
        click.secho(f"Error: File not found - {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        if verbose:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@click.group()
def cli():
    """UML Enhancing Tool CLI"""
    pass


@cli.command()
def version():
    """Show version information."""
    from src import __version__

    click.echo(f"UML Enhancing Tool v{__version__}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file):
    """Validate a PlantUML diagram file."""
    from src.parser import PlantUMLParser

    click.echo(f"Validating: {input_file}")

    try:
        with open(input_file, "r") as f:
            content = f.read()

        parser = PlantUMLParser()
        result = parser.parse(content)

        click.secho("✓ Valid PlantUML diagram", fg="green")
        click.echo(f"  - Classes: {len(result['classes'])}")
        click.echo(f"  - Relationships: {len(result['relationships'])}")

    except Exception as e:
        click.secho(f"✗ Invalid diagram: {e}", fg="red")
        sys.exit(1)


if __name__ == "__main__":
    # If run directly, use the main command
    if len(sys.argv) == 1:
        main(["--help"])
    else:
        main()
