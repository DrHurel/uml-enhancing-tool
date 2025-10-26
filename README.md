# UML Enhancing Tool

A tool that implements a pipeline to enhance UML diagrams using Formal Concept Analysis (FCA) and AI techniques.

## Overview

This tool processes UML diagrams written in PlantUML language (including support for cardinality) and enhances them by:

1. **Parsing**: Transforms PlantUML diagrams into knowledge graphs
2. **FCA Analysis**: Extracts formal concepts using FCA4J
3. **Concept Identification**: Creates abstract concepts based on concept relevance
4. **LLM Naming**: Names abstract classes using a Large Language Model
5. **Generation**: Produces enhanced PlantUML diagrams with abstract classes

## Features

- **PlantUML Support**: Parse diagrams with classes, relationships, and cardinality
- **Knowledge Graph**: Transform UML into graph representation for analysis
- **Formal Concept Analysis**: Extract meaningful patterns using FCA4J
- **AI-Powered Naming**: Generate semantic names for abstract classes using LLMs
- **Evaluation Metrics**: Automatic generation of quality assessment CSV files
- **Comprehensive Reporting**: Detailed logs and reports for each pipeline step
- **90%+ Test Coverage**: Built with TDD approach for reliability

## Installation

```bash
# Clone the repository
git clone https://github.com/DrHurel/uml-enhancing-tool.git
cd uml-enhancing-tool

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with your LLM API keys:

```
OPENAI_API_KEY=your_openai_key
# or
ANTHROPIC_API_KEY=your_anthropic_key
```

## Usage

```bash
# Run the pipeline
python main.py --input diagram.puml --output enhanced_diagram.puml

# With custom settings
python main.py --input diagram.puml --output enhanced.puml --min-relevance 15 --verbose

# View detailed help
python main.py --help
```

### Output Files

After running the pipeline, check the following directories:

- **`output/`**: Enhanced PlantUML diagrams
- **`reports/`**: 
  - `evaluation_*.csv` - Quality assessment template (see [EVALUATION.md](EVALUATION.md))
  - `evaluation_simple_*.csv` - Automated metrics summary
  - `concepts_*.json` - FCA analysis results
  - `abstract_classes_*.json` - Generated abstractions
  - `results_*.json` - Pipeline execution summary
- **`logs/`**: Detailed execution logs

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
```

## Project Structure

```
uml-enhancing-tool/
├── src/
│   ├── parser/          # PlantUML parsing
│   ├── knowledge_graph/ # Knowledge graph transformation
│   ├── fca_analyzer/    # FCA analysis
│   ├── llm_naming/      # LLM-based naming
│   ├── generator/       # PlantUML generation
│   ├── pipeline/        # Pipeline orchestration
│   └── utils/           # Utilities and helpers
├── tests/               # Test suite
├── output/              # Generated diagrams
├── logs/                # Pipeline logs
├── reports/             # Analysis reports
└── main.py              # CLI entry point
```

## Development

This project follows Test-Driven Development (TDD) practices:

- Write tests first
- Maintain 90%+ code coverage
- All tests must pass before merging

## CI/CD

GitHub Actions automatically runs tests and generates coverage reports on every push and pull request.

## License

[Add your license here]
