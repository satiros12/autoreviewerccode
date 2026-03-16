# CExams - C Programming Exam Evaluation System

## Project Structure

```
CExams/
├── Exams/                    # Exam files (.c files)
├── criteria/                 # Evaluation criteria and rubrics
│   ├── evaluation_improved.json
│   ├── OLD/                  # Deprecated criteria files
│   └── OLD_IP1/              # Old IP1 rubrics
├── src/                      # Source code package
│   └── cexams/
│       ├── __init__.py
│       ├── __main__.py       # CLI entry point
│       ├── api/
│       │   └── client.py     # OpenRouter API client
│       ├── core/
│       │   └── reviewer.py   # Core review logic
│       └── models/
│           └── criteria.py   # Data models
├── tests/                    # Test files
│   ├── test_models.py
│   └── test_api_client.py
├── config/
│   └── pyproject.toml
├── docs/
│   ├── INSTRUCTIONS.md
│   └── Exam_Description.txt
└── reviews/                 # JSON review outputs
```

## Quick Start

1. **Set up API key:**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

2. **Run the exam reviewer:**
   ```bash
   python -m cexams
   ```

3. **Check results:**
   Results will be saved in `reviews/` folder as JSON files.

## CLI Options

```bash
python -m cexams [OPTIONS]

Options:
  --exams-dir TEXT       Directory containing exam files (default: Exams)
  --criteria-file TEXT   Path to evaluation criteria JSON file (default: criteria/evaluation_improved.json)
  --output-dir TEXT      Directory to save review results (default: reviews)
  --test-mode            Run in test mode (single exam, single criteria)
  --verbose, -v          Enable verbose logging
  --model TEXT           AI model to use (default: deepseek/deepseek-chat)
  --help                 Show this message and exit
```

## Evaluation Criteria

Criteria are defined in `criteria/evaluation_improved.json` with 7 main categories:
1. Code structure and formatting
2. Structure declaration and usage
3. Enum and typedef usage
4. Command line arguments (argc/argv)
5. Function implementation
6. Additional functions
7. Compilation and execution

## Dependencies

- Python 3.12+
- `requests` library
- `urllib3` library

Install with:
```bash
pip install -e ".[dev]"
```

## Development

### Running Tests
```bash
pytest
```

### Linting
```bash
ruff check src/
```

## Usage Examples

```bash
# Test with limited scope
python -m cexams --test-mode

# Full review with custom directories
python -m cexams --exams-dir MyExams --output-dir MyReviews

# Verbose output
python -m cexams --verbose
```

## Output

JSON reviews are saved in `reviews/[exam_name]_review.json` with:
- Exam metadata
- Criteria evaluations
- Scores and justifications
- Subsection analyses

## Notes

- API calls use OpenRouter DeepSeek model by default
- Rate limiting: 1 second between API calls
- Error handling continues processing other exams
- Cost estimate: < $0.50 for 10 exams × 7 criteria