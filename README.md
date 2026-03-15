# C Exam Grader

Automatic C exam evaluation and grading system.

## Features

- Parse evaluation criteria from CSV files
- Generate detailed rubrics based on exam requirements
- Analyze C code for syntax, structure, and functionality
- Automatically grade exams based on predefined criteria
- Generate detailed evaluation reports

## Project Structure

```
.
├── src/cexam_grader/     # Main source code
├── tests/               # Test files
├── data/               # Data files and configurations
├── Exams/              # Exam submissions
├── IP1_RUB/            # Example rubrics
├── evaluation.json     # Initial evaluation structure
└── evaluation_criteria.csv # Evaluation criteria
```

## Installation

```bash
uv sync
```

## Usage

```bash
uv run cexam-grader --help
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check src/