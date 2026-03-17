# CExams AI Reviewer - Instructions

## Overview
This Python script automatically reviews C programming exams using AI (OpenRouter DeepSeek model). It reads each exam from the `Exams/` folder, evaluates them against criteria from `evaluation_improved.json`, and saves detailed reviews in the `JSON_REVIEWS/` folder.

## Files Created
- `exam_reviewer.py` - Main script for reviewing exams
- `test_exam_reviewer.py` - Test script to verify functionality
- `INSTRUCTIONS.md` - This instructions file

## Prerequisites
1. Python 3.12 or higher
2. OpenRouter API key (free tier available)
3. Required Python packages: `requests`

## Setup Instructions

### 1. Get OpenRouter API Key
1. Go to https://openrouter.ai/
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes credits for testing

### 2. Configure the Script
Edit `exam_reviewer.py` and update the API key:

```python
# Line 265 in exam_reviewer.py
OPENROUTER_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"
```

Replace `"YOUR_ACTUAL_API_KEY_HERE"` with your actual OpenRouter API key.

### 3. Install Dependencies
If `requests` is not installed:
```bash
pip install requests
```

## Usage

### Basic Usage
Run the main script:
```bash
python exam_reviewer.py
```

### What Happens
1. Script loads criteria from `evaluation_improved.json` (7 criteria found)
2. Scans `Exams/` folder for `.c` files (10 files found)
3. For each exam:
   - Reads the C code
   - For each criteria:
     - Creates AI prompt with code and criteria details
     - Calls OpenRouter DeepSeek API
     - Parses JSON response
   - Calculates overall score
   - Saves results to `JSON_REVIEWS/[exam_name]_review.json`

### Output Structure
Each review file contains:
```json
{
  "exam_name": "filename_without_extension",
  "exam_file": "original_filename.c",
  "total_criteria": 7,
  "criteria_evaluations": [
    {
      "criteria_index": 1,
      "criteria_title": "Criteria title",
      "criteria_description": "Criteria description",
      "maximum_score": 1.0,
      "awarded_score": 0.75,
      "justification": "AI evaluation explanation",
      "subsection_evaluations": [...]
    }
  ],
  "overall_score": 5.25,
  "maximum_possible_score": 10.0
}
```

## Testing
Run the test script first to verify everything works:
```bash
python test_exam_reviewer.py
```

This verifies:
- File structure and permissions
- Criteria loading
- Prompt generation
- JSON parsing
- Output file creation

## File Structure
```
CExams/
├── exam_reviewer.py          # Main review script
├── test_exam_reviewer.py     # Test script
├── INSTRUCTIONS.md          # This file
├── evaluation_improved.json  # Evaluation criteria
├── Exams/                   # Input exam files (.c)
│   ├── exam1.c
│   ├── exam2.c
│   └── ...
└── JSON_REVIEWS/            # Output review files (.json)
    ├── exam1_review.json
    ├── exam2_review.json
    └── ...
```

## Cost Estimate
- Each exam has 7 criteria
- Each API call processes 1 criteria
- 10 exams × 7 criteria = 70 API calls
- DeepSeek model cost: ~$0.14 per 1M tokens
- Estimated cost for 10 exams: < $0.50

## Error Handling
The script includes comprehensive error handling:
- API connection failures
- Invalid JSON responses
- File access issues
- Rate limiting (1 second delay between API calls)
- Continues processing other exams if one fails

## Customization

### Modify Criteria
Edit `evaluation_improved.json` to change evaluation criteria.

### Change AI Model
Edit line 27 in `exam_reviewer.py`:
```python
self.model = "deepseek/deepseek-chat"  # Change to another model
```

### Adjust API Parameters
Edit lines 149-153 in `exam_reviewer.py`:
```python
"temperature": 0.1,      # Lower = more consistent
"max_tokens": 2000       # Response length limit
```

## Notes
1. The script includes rate limiting (1 second delay) to avoid API limits
2. All API calls include error logging
3. Results are saved after each exam review
4. If interrupted, you can rerun - completed reviews won't be duplicated
5. Check `JSON_REVIEWS/` folder for results

## Support
If you encounter issues:
1. Check API key is valid
2. Ensure internet connection
3. Verify file permissions
4. Run test script for diagnostics

## Example Run
```
$ python exam_reviewer.py
CExams AI Reviewer
==================================================
Loading criteria from evaluation_improved.json...
Scanning exam files in Exams...
Found 10 exam files to review

==================================================
Reviewing exam 1/10: student_exam_1.c
==================================================
✓ Review completed: student_exam_1
  Score: 6.50/10.00
  Results saved to: JSON_REVIEWS/student_exam_1_review.json

[... continues with other exams ...]

All exams reviewed successfully!
Results saved in: JSON_REVIEWS
```