# AGENTS.md - Developer Documentation

## Project Overview

CExams is an AI-powered C programming exam evaluation system that uses OpenRouter's DeepSeek model to evaluate student exam submissions against defined criteria.

## Running the Project

### Basic Usage
```bash
python -m cexams
```

### With API Key
```bash
export OPENROUTER_API_KEY="your-key"
python -m cexams
```

### Options
```bash
python -m cexams --help
```

## Project Structure

```
src/cexams/
├── __init__.py         # Package version
├── __main__.py         # CLI entry point with argparse
├── api/
│   └── client.py       # OpenRouter API client with retry logic
├── core/
│   └── reviewer.py     # ExamReviewer, CriteriaLoader, PromptGenerator
└── models/
    └── criteria.py     # Data models (Criteria, ExamReview, etc.)
```

## Key Components

### ExamReviewer (core/reviewer.py)
- Main class for reviewing exams
- `review_exam(exam_path, criteria_list)` - Reviews a single exam
- `save_review(review, output_dir)` - Saves results to JSON

### OpenRouterClient (api/client.py)
- Handles API calls to OpenRouter
- Automatic retry with exponential backoff
- Response parsing (handles markdown code blocks)

### Data Models (models/criteria.py)
- `Criteria` - Evaluation criteria with subsections
- `ExamReview` - Complete review results
- `CriteriaEvaluation` - Single criteria evaluation result

## Testing

Run tests with:
```bash
pytest
```

## Linting

Run ruff with:
```bash
ruff check src/
```

## Common Tasks

### Add New Criteria
Edit `criteria/evaluation_improved.json` following the existing format.

### Change AI Model
```bash
python -m cexams --model anthropic/claude-3-sonnet
```

### Add New Subsection to Criteria
Update the JSON file with new subsections, including:
- `nombre`: Subsection name
- `descripcion`: Description
- `puntos`: Point value
- `penalizacion_min`: Minimum penalty
- `anulador`: Whether it's a nullifier
