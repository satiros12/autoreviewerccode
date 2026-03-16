#!/usr/bin/env python3
"""
Test the full pipeline with limited scope (1 exam, 2 criteria)
"""

import os
import sys

# Add current directory to path to import exam_reviewer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Modify the exam_reviewer to limit scope
original_exam_reviewer = """
import os
import json
import time
import logging
from typing import Dict, List, Any
import requests

# IMPORTANT: Replace with your actual OpenRouter API key
# You should get this from https://openrouter.ai/
try:
    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
except KeyError:
    OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY_HERE"
# Configuration
EXAMS_DIR = "Exams"
CRITERIA_FILE = "evaluation_improved.json"
OUTPUT_DIR = "JSON_REVIEWS"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExamReviewer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-chat"
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cexams.local",
            "X-Title": "CExams AI Reviewer"
        }
    
    def load_criteria(self, criteria_file: str) -> List[Dict]:
        try:
            with open(criteria_file, 'r', encoding='utf-8') as f:
                criteria = json.load(f)
            logger.info(f"Loaded {len(criteria)} criteria from {criteria_file}")
            return criteria
        except Exception as e:
            logger.error(f"Error loading criteria: {e}")
            raise
    
    def read_exam_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read exam file: {file_path} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error reading exam file {file_path}: {e}")
            raise
    
    def create_prompt(self, exam_content: str, criteria: Dict) -> str:
        prompt = f\"\"\"You are evaluating a C programming exam submission based on specific criteria.

EXAM CODE:
```c
{exam_content}
```

CRITERIA TO EVALUATE:
Title: {criteria.get('titulo', 'N/A')}
Description: {criteria.get('descripcion', 'N/A')}
Maximum Score: {criteria.get('nota_maxima', 'N/A')}

Subsections:
\"\"\"
        
        for i, sub in enumerate(criteria.get('subapartados', []), 1):
            prompt += f\"\\n{i}. {sub.get('nombre', 'N/A')}: {sub.get('descripcion', 'N/A')}\"
            prompt += f\" (Points: {sub.get('puntos', 'N/A')})\"
            if sub.get('anulador', False):
                prompt += \" [NULLIFIER - Can void entire criteria]\"
        
        prompt += \"\"\"

INSTRUCTIONS:
1. Analyze the C code against each subsection above
2. For each subsection, determine if it's implemented correctly
3. Assign points based on the specified point values
4. If a NULLIFIER subsection applies, the entire criteria may get 0 points
5. Provide a clear justification for your evaluation

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
    \"criteria_title\": \"string\",
    \"criteria_description\": \"string\",
    \"maximum_score\": number,
    \"awarded_score\": number,
    \"justification\": \"string explaining the score\",
    \"subsection_evaluations\": [
        {
            \"subsection_name\": \"string\",
            \"subsection_description\": \"string\",
            \"possible_points\": number,
            \"awarded_points\": number,
            \"reasoning\": \"string explaining the points\"
        }
    ]
}

IMPORTANT: Return ONLY valid JSON, no other text.\"\"\"
        
        return prompt
    
    def call_ai_api(self, prompt: str) -> str:
        data = {
            \"model\": self.model,
            \"messages\": [
                {\"role\": \"system\", \"content\": \"You are an expert C programming evaluator. Analyze code and provide detailed evaluations in JSON format.\"},
                {\"role\": \"user\", \"content\": prompt}
            ],
            \"temperature\": 0.1,
            \"max_tokens\": 2000
        }
        
        try:
            logger.info(\"Calling OpenRouter AI API...\")
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            logger.info(\"AI API call successful\")
            
            return ai_response
            
        except Exception as e:
            logger.error(f\"API request failed: {e}\")
            raise
    
    def parse_ai_response(self, response_text: str) -> Dict:
        try:
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            result = json.loads(cleaned_response)
            return result
            
        except Exception as e:
            logger.error(f\"Failed to parse AI response as JSON: {e}\")
            raise
    
    def review_exam(self, exam_path: str, criteria_list: List[Dict]) -> Dict:
        exam_name = os.path.splitext(os.path.basename(exam_path))[0]
        logger.info(f\"Starting review for: {exam_name}\")
        
        try:
            exam_content = self.read_exam_file(exam_path)
            
            results = {
                \"exam_name\": exam_name,
                \"exam_file\": os.path.basename(exam_path),
                \"total_criteria\": len(criteria_list),
                \"criteria_evaluations\": [],
                \"overall_score\": 0,
                \"maximum_possible_score\": 0
            }
            
            for i, criteria in enumerate(criteria_list, 1):
                logger.info(f\"Evaluating criteria {i}/{len(criteria_list)}: {criteria.get('titulo', 'Unknown')}\")
                
                try:
                    prompt = self.create_prompt(exam_content, criteria)
                    ai_response = self.call_ai_api(prompt)
                    evaluation = self.parse_ai_response(ai_response)
                    evaluation[\"criteria_index\"] = i
                    
                    results[\"criteria_evaluations\"].append(evaluation)
                    results[\"overall_score\"] += evaluation.get(\"awarded_score\", 0)
                    results[\"maximum_possible_score\"] += criteria.get(\"nota_maxima\", 0)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f\"Error evaluating criteria {i}: {e}\")
                    error_eval = {
                        \"criteria_index\": i,
                        \"criteria_title\": criteria.get('titulo', 'Unknown'),
                        \"error\": str(e),
                        \"awarded_score\": 0
                    }
                    results[\"criteria_evaluations\"].append(error_eval)
                    results[\"maximum_possible_score\"] += criteria.get(\"nota_maxima\", 0)
            
            logger.info(f\"Completed review for {exam_name}. Score: {results['overall_score']}/{results['maximum_possible_score']}\")
            return results
            
        except Exception as e:
            logger.error(f\"Failed to review exam {exam_path}: {e}\")
            raise
    
    def save_results(self, results: Dict, output_dir: str = \"JSON_REVIEWS\"):
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            exam_name = results[\"exam_name\"]
            filename = f\"{exam_name}_review.json\"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f\"Saved review results to: {filepath}\")
            return filepath
            
        except Exception as e:
            logger.error(f\"Error saving results: {e}\")
            raise


def main_limited():
    \"\"\"Limited test version\"\"\"
    print(\"CExams AI Reviewer - Limited Test\")
    print(\"=\" * 50)
    
    if not os.environ.get(\"OPENROUTER_API_KEY\"):
        print(\"\\nERROR: OPENROUTER_API_KEY environment variable not set\")
        return
    
    reviewer = ExamReviewer(os.environ[\"OPENROUTER_API_KEY\"])
    
    try:
        print(f\"Loading criteria from evaluation_improved.json...\")
        all_criteria = reviewer.load_criteria(\"evaluation_improved.json\")
        
        # LIMIT: Use only first 2 criteria for testing
        test_criteria = all_criteria[:2]
        print(f\"Using {len(test_criteria)} criteria for testing (out of {len(all_criteria)})\")
        
        exam_files = []
        for file in os.listdir(\"Exams\"):
            if file.endswith('.c'):
                exam_files.append(os.path.join(\"Exams\", file))
        
        if not exam_files:
            print(f\"No exam files found in Exams\")
            return
        
        # LIMIT: Use only first exam for testing
        test_exam = exam_files[0]
        print(f\"\\nTesting with exam: {os.path.basename(test_exam)}\")
        print(f\"=\" * 50)
        
        results = reviewer.review_exam(test_exam, test_criteria)
        output_path = reviewer.save_results(results, \"JSON_REVIEWS_TEST\")
        
        print(f\"\\n✓ Review completed!\")
        print(f\"  Exam: {results['exam_name']}\")
        print(f\"  Score: {results['overall_score']:.2f}/{results['maximum_possible_score']:.2f}\")
        print(f\"  Results saved to: {output_path}\")
        
        # Show brief summary
        print(f\"\\nCriteria Evaluations:\")
        for eval in results[\"criteria_evaluations\"]:
            if \"error\" in eval:
                print(f\"  - {eval.get('criteria_title', 'Unknown')}: ERROR - {eval['error'][:50]}...\")
            else:
                print(f\"  - {eval.get('criteria_title', 'Unknown')}: {eval.get('awarded_score', 0)}/{eval.get('maximum_score', 0)}\")
        
    except Exception as e:
        print(f\"\\nERROR: {e}\")
        import traceback
        traceback.print_exc()
"""

# Write modified version
exec(original_exam_reviewer)

if __name__ == "__main__":
    main_limited()
