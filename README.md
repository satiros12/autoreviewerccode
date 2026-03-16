# CExams - C Programming Exam Evaluation System

## Project Structure

```
CExams/
├── Exams/                    # Exam files (.c files)
├── criteria/                 # Evaluation criteria and rubrics
│   ├── evaluation_improved.json
│   ├── evaluation.json
│   ├── evaluation_criteria.csv
│   └── IP1_RUB/             # Additional rubric files
├── scripts/                  # Python scripts
│   ├── exam_reviewer.py     # Main review script
│   ├── main.py              # Entry point
│   ├── quick_test.py        # Quick test script
│   └── test_*.py            # Various test scripts
├── reviews/                  # JSON review outputs
├── tests/                    # Test files (to be populated)
├── docs/                     # Documentation
│   ├── INSTRUCTIONS.md
│   └── Exam_Description.txt
├── config/                   # Configuration files
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .python-version
├── src/                      # Source code package
│   └── cexams/
└── .git/                     # Git repository
```

## Quick Start

1. **Set up API key:**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

2. **Run the exam reviewer:**
   ```bash
   python scripts/exam_reviewer.py
   ```

3. **Check results:**
   Results will be saved in `reviews/` folder as JSON files.

## Scripts Overview

- `scripts/exam_reviewer.py` - Main AI-powered exam reviewer
- `scripts/main.py` - Simple entry point
- `scripts/test_*.py` - Various test scripts

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

Install with:
```bash
pip install requests
```

## Usage Example

```bash
# Test with limited scope
export TEST_MODE=true
python scripts/exam_reviewer.py

# Full review
unset TEST_MODE
python scripts/exam_reviewer.py
```

## Output

JSON reviews are saved in `reviews/[exam_name]_review.json` with:
- Exam metadata
- Criteria evaluations
- Scores and justifications
- Subsection analyses

## Notes

- API calls use OpenRouter DeepSeek model
- Rate limiting: 1 second between API calls
- Error handling continues processing other exams
- Cost estimate: < $0.50 for 10 exams × 7 criteria