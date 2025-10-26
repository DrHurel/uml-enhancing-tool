# Changelog

All notable changes to the UML Enhancing Tool project.

## [Unreleased]

### Added
- **Inherited Attribute Removal**: Child classes automatically have inherited attributes and methods removed from their definitions, reducing redundancy and improving diagram clarity
- **Evaluation CSV Export**: Automatic generation of quality assessment CSV files for each pipeline run
  - `evaluation_*.csv`: Full template with manual evaluation columns
  - `evaluation_simple_*.csv`: Simplified metrics-only version
- **Quality Metrics**: 
  - Name Relevance Score (NRS) [0..1]: Measures how well the class name describes the concept
  - Abstraction Relevance Score (ARS) [0..1]: Measures the value of extracting the abstraction
  - Automated justifications for all scores
- **Cardinality Support**: Enhanced parser to correctly handle PlantUML relationship cardinality syntax
- **Hierarchical Concept Analysis**: FCA lattice traversal to infer objects for concepts with empty extent
- **Class Subsumption Logic**: Automatically includes classes that have all features of an abstraction plus additional features

### Changed
- **Parser**: Improved relationship parsing with regex to correctly extract class names, cardinality, and labels
- **Generator**: Enhanced to properly format cardinality in PlantUML syntax
- **FCA Analyzer**: Now extracts both attributes AND methods for more comprehensive analysis
- **Knowledge Graph**: Exports both attributes and methods to FCA formal context

### Fixed
- Cardinality parsing bug where cardinality values were mistaken for class names
- Relationship generation syntax errors
- PlantUML syntax validation issues
- Missing abstractions due to FCA filtering

## Examples

### Inherited Attribute Removal

**Before:**
```plantuml
class University {
  +name: String          <- Redundant (inherited from AbstractName)
  +address: String
  +founded: int
  +enroll()
  +graduate()
}
```

**After:**
```plantuml
abstract class AbstractName {
  +name: String
}

class University {
  +address: String       <- Only unique attributes remain
  +founded: int
  +enroll()
  +graduate()
}

University --|> AbstractName
```

### Evaluation Output

```csv
Id Concept: C_20251026_130712_1
Concept name: AbstractName
Name justification: Common attributes: +name. Shared by 5 classes.
NRS: 0.4 - Generic name derived from common attribute
ARS: 0.82 - Highly valuable abstraction: 5 classes share 1 features
Extent: University, Department, Professor, Student, Library
Intent: +name: String
```

## Migration Guide

No breaking changes. All existing diagrams will work with the new version and will benefit from:
1. Cleaner output with no duplicated attributes
2. Automatic evaluation metrics
3. Better cardinality handling
