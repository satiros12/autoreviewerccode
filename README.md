# CExams - C Programming Exam Evaluation System

AI-powered C programming exam evaluation system with both CLI and web interface.

## Project Structure

```
CExams/
├── Exams/                       # Original exam files (.c files)
├── criteria/                    # Evaluation criteria JSON files
│   └── evaluation_improved.json
├── src/                         # CLI source code
│   └── cexams/
├── web_interface/               # Web application
│   ├── app.py                   # Flask application
│   ├── config.py                # Configuration
│   ├── routes/                  # API routes
│   ├── services/                # Business logic
│   ├── templates/               # HTML templates
│   ├── exams/                   # Uploaded exam files
│   ├── criteria_db/             # Individual criteria storage
│   ├── annotated_exams/         # Annotated exam files
│   └── reviews/                 # Review results
├── tests/                       # Test files
└── docs/                        # Documentation
```

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Set the OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## CLI Usage

```bash
python -m cexams [OPTIONS]

Options:
  --exams-dir TEXT       Directory containing exam files
  --criteria-file TEXT  Path to evaluation criteria JSON file
  --output-dir TEXT     Directory to save review results
  --test-mode           Run in test mode (single exam, single criteria)
  --verbose, -v         Enable verbose logging
  --model TEXT          AI model to use (default: deepseek/deepseek-chat)
  --help                Show this message and exit
```

## Web Interface

Start the web server:

```bash
cd web_interface
python app.py
```

The web interface will be available at `http://localhost:5000`

### Features

- **Upload Exams**: Upload .c exam files for evaluation
- **Upload Criteria**: Upload evaluation criteria (single object or array of criteria)
- **Run Evaluation**: Execute automatic exam evaluation with configurable options:
  - Select specific exam or all exams
  - Select specific criteria, all criteria, or "Only Annotate" mode
  - Configure number of threads for parallel processing
  - Option to generate reviewer annotations with `//REVIEWER:` comments
- **Interactive Reviewer**: Manually review and edit evaluations:
  - View exam code with syntax highlighting
  - Navigate between exams and criteria
  - Edit scores and justifications
  - Toggle between original and annotated code
- **Download Results**: Download reviews as JSON or text format

### Web Interface Routes

| Route | Description |
|-------|-------------|
| `/` | Home page with upload forms |
| `/run` | Run evaluation page |
| `/reviewer` | Interactive reviewer |
| `/reviews` | View all review results |
| `/exams` | Manage exam files |
| `/criteria` | Manage evaluation criteria |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/files/exams` | GET | List all exam files |
| `/api/files/criteria` | GET | List all criteria files |
| `/api/criteria/list` | GET | List all criteria with details |
| `/api/run/single` | POST | Run single exam review |
| `/api/run/parallel` | POST | Run parallel review |
| `/api/annotate` | POST | Generate annotations for exam |
| `/api/annotated-exam/<filename>` | GET | Get annotated exam |
| `/api/reviewer/data` | GET | Get reviewer data |
| `/api/reviewer/save-evaluation` | POST | Save evaluation |

## Evaluation Criteria

Criteria are stored as individual JSON files in `criteria_db/`. Each criteria contains:

- `titulo`: Criteria title
- `descripcion`: Description
- `nota_maxima`: Maximum score
- `subapartados`: Array of subsections with:
  - `nombre`: Subsection name
  - `descripcion`: Description
  - `puntos`: Point value
  - `penalizacion_min`: Minimum penalty
  - `anulador`: Whether it's a nullifier

## Annotation Feature

When enabled, the system generates annotated versions of exams with `//REVIEWER:` comments indicating:
- Syntax errors
- Logic errors
- Bugs
- Style issues
- Missing error handling
- Memory issues

Annotated files are stored in `annotated_exams/` directory with `_annotated.c` suffix.

## Development

### Running Tests
```bash
pytest
```

### Linting
```bash
ruff check src/
ruff check web_interface/
```

## Output

JSON reviews are saved with structure:
```json
{
  "exam_name": "exam_filename",
  "exam_file": "exam_filename.c",
  "total_criteria": 7,
  "criteria_evaluations": [...],
  "overall_score": 85.0,
  "maximum_possible_score": 100.0
}
```

Each criteria evaluation contains:
- Criteria title and description
- Awarded score
- Justification
- Subsection evaluations

## Notes

- API calls use OpenRouter DeepSeek model by default
- Rate limiting is applied between API calls
- Error handling continues processing other exams
- The web interface stores data in separate directories from the CLI
