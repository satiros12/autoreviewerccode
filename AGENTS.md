# C Exam Grader - Agent Instructions

## Project Overview
A Python-based system for automatically reviewing C programming exams with UV and Git integration.

## Key Components Built

### 1. Project Infrastructure
- Git repository initialized with main branch
- UV project setup with proper dependencies
- Project structure: `src/cexam_grader/`, `tests/`, `data/`
- Dependencies: pandas, click, rich, pytest

### 2. Rubric Generator (`rubric_generator.py`)
- Parses evaluation criteria from CSV files
- Generates detailed rubrics based on exam requirements
- Supports both CSV format and existing JSON rubric templates
- Creates structured rubrics with criteria, rules, and penalties
- Handles multiple rubric formats (evaluation.json and IP1_RUB styles)

### 3. Exam Analyzer (`exam_analyzer.py`)
- Analyzes C code for compilation and structure
- Extracts student information from filenames and content
- Checks compilation with gcc (Wall, Wextra, Werror flags)
- Analyzes code structure: indentation, comments, functions, variables
- Detects common issues: mixed tabs/spaces, uninitialized variables, etc.

### 4. Exam Evaluator (`exam_analyzer.py`)
- Evaluates exams using generated or existing rubrics
- Applies penalties based on detected issues
- Generates detailed evaluation reports
- Calculates scores and grades (A-F scale)
- Saves evaluations as JSON files

### 5. CLI Interface (`cli.py`)
- **`generate-rubric`**: Generate rubrics from CSV criteria
- **`inspect-rubric`**: View existing rubric details
- **`list-templates`**: List available rubric templates
- **`evaluate`**: Evaluate one or more exam files
- Supports verbose output for detailed analysis
- Handles multiple exam files simultaneously

## Usage Examples

```bash
# Generate rubric from CSV
python -m src.cexam_grader.cli generate-rubric --name "Exam Rubric"

# Inspect existing rubric
python -m src.cexam_grader.cli inspect-rubric --json evaluation.json

# Evaluate exam files
python -m src.cexam_grader.cli evaluate "Exams/*.c" --rubric evaluation.json

# Evaluate with verbose output
python -m src.cexam_grader.cli evaluate "Exams/exam.c" --rubric evaluation.json --verbose
```

## File Structure

```
cexam_grader/
├── src/cexam_grader/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── rubric_generator.py # Rubric generation
│   └── exam_analyzer.py    # Code analysis & evaluation
├── tests/                  # Test files
├── data/                   # Data files
├── Exams/                  # Exam submissions (existing)
├── IP1_RUB/               # Example rubrics (existing)
├── evaluation.json        # Initial evaluation structure
├── evaluation_criteria.csv # Evaluation criteria
├── pyproject.toml         # UV project config
├── README.md              # Project documentation
└── AGENTS.md              # This file
```

## Testing Commands

```bash
# Install dependencies
uv sync

# Run CLI commands
python -m src.cexam_grader.cli --help

# Generate and test rubric
python -m src.cexam_grader.cli generate-rubric --output test_rubric.json

# Evaluate sample exams
python -m src.cexam_grader.cli evaluate "Exams/*.c" --rubric evaluation.json
```

## Git Commit History
1. Initial project setup with uv and git
2. Add rubric generator and CLI interface
3. Add exam analyzer and complete CLI implementation
4. Fix evaluation.json format handling and complete testing

## Next Steps (For User to Specify)
Based on the user's instructions, they will now indicate how to continue with:
1. Further refinement of the rubric generation
2. Additional analysis features for C code
3. Integration with specific grading workflows
4. Report generation in different formats
5. Batch processing of multiple exams