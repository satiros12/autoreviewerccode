import os
import json
import time
import logging
from typing import Dict, Any, List

from config import OPENROUTER_API_KEY, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or DEFAULT_MODEL
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cexams.local",
            "X-Title": "CExams AI Reviewer",
        }

    def call_api(self, prompt: str, system_prompt: str = "") -> str:
        import requests

        if not system_prompt:
            system_prompt = (
                "You are an expert C programming evaluator. "
                "Analyze code and provide detailed evaluations in JSON format."
            )

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    @staticmethod
    def parse_ai_response(response_text: str) -> Dict[str, Any]:
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise


class ExamEvaluator:
    def __init__(self, criteria_dir: str, exams_dir: str, reviews_dir: str):
        self.criteria_dir = criteria_dir
        self.exams_dir = exams_dir
        self.reviews_dir = reviews_dir

        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set")
        self.api_client = OpenRouterClient()

    def load_criteria(self, criteria_file: str) -> List[Dict]:
        filepath = os.path.join(self.criteria_dir, criteria_file)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_exam(self, exam_file: str) -> str:
        filepath = os.path.join(self.exams_dir, exam_file)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def create_prompt(self, exam_content: str, criteria: Dict) -> str:
        prompt = f"""You are evaluating a C programming exam submission.

EXAM CODE:
```c
{exam_content}
```

CRITERIA TO EVALUATE:
Title: {criteria.get("titulo", "")}
Description: {criteria.get("descripcion", "")}
Maximum Score: {criteria.get("nota_maxima", 0)}

Subsections:
"""

        for i, sub in enumerate(criteria.get("subapartados", []), 1):
            prompt += f"\n{i}. {sub.get('nombre', '')}: {sub.get('descripcion', '')}"
            prompt += f" (Points: {sub.get('puntos', 0)})"
            if sub.get("anulador"):
                prompt += " [NULLIFIER]"

        prompt += """

OUTPUT FORMAT (JSON only):
{
    "criteria_title": "string",
    "criteria_description": "string",
    "maximum_score": number,
    "awarded_score": number,
    "justification": "string",
    "subsection_evaluations": [
        {
            "subsection_name": "string",
            "subsection_description": "string",
            "possible_points": number,
            "awarded_points": number,
            "reasoning": "string"
        }
    ]
}
"""
        return prompt

    def run_single_review(self, exam_file: str, criteria_file: str) -> Dict:
        exam_content = self.load_exam(exam_file)
        criteria_list = self.load_criteria(criteria_file)

        evaluations = []
        overall_score = 0.0
        max_score = 0.0

        for i, criteria in enumerate(criteria_list):
            prompt = self.create_prompt(exam_content, criteria)

            try:
                ai_response = self.api_client.call_api(prompt)
                evaluation = self.api_client.parse_ai_response(ai_response)
            except Exception as e:
                logger.error(f"Evaluation failed for criteria {i}: {e}")
                evaluation = {
                    "criteria_title": criteria.get("titulo", ""),
                    "criteria_description": criteria.get("descripcion", ""),
                    "maximum_score": criteria.get("nota_maxima", 0),
                    "awarded_score": 0,
                    "justification": f"Error: {str(e)}",
                    "subsection_evaluations": [],
                }

            evaluation["criteria_index"] = i + 1
            evaluations.append(evaluation)
            overall_score += evaluation.get("awarded_score", 0)
            max_score += criteria.get("nota_maxima", 0)

            time.sleep(1)

        review = {
            "exam_name": os.path.splitext(exam_file)[0],
            "exam_file": exam_file,
            "total_criteria": len(criteria_list),
            "criteria_evaluations": evaluations,
            "overall_score": overall_score,
            "maximum_possible_score": max_score,
        }

        output_file = os.path.join(
            self.reviews_dir, f"{os.path.splitext(exam_file)[0]}_review.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(review, f, indent=2, ensure_ascii=False)

        return review

    def run_single_criteria_review(
        self, exam_file: str, criteria_file: str, criteria_index: int = 0
    ) -> Dict:
        exam_content = self.load_exam(exam_file)
        criteria_list = self.load_criteria(criteria_file)

        if criteria_index >= len(criteria_list):
            raise ValueError(f"Criteria index {criteria_index} out of range")

        criteria = criteria_list[criteria_index]
        prompt = self.create_prompt(exam_content, criteria)

        try:
            ai_response = self.api_client.call_api(prompt)
            evaluation = self.api_client.parse_ai_response(ai_response)
        except Exception as e:
            logger.error(f"Evaluation failed for criteria {criteria_index}: {e}")
            evaluation = {
                "criteria_title": criteria.get("titulo", ""),
                "criteria_description": criteria.get("descripcion", ""),
                "maximum_score": criteria.get("nota_maxima", 0),
                "awarded_score": 0,
                "justification": f"Error: {str(e)}",
                "subsection_evaluations": [],
            }

        evaluation["criteria_index"] = criteria_index + 1

        review_file = os.path.join(
            self.reviews_dir, f"{os.path.splitext(exam_file)[0]}_review.json"
        )

        if os.path.exists(review_file):
            with open(review_file, "r", encoding="utf-8") as f:
                review_data = json.load(f)
        else:
            review_data = {
                "exam_name": os.path.splitext(exam_file)[0],
                "exam_file": exam_file,
                "total_criteria": len(criteria_list),
                "criteria_evaluations": [],
                "overall_score": 0.0,
                "maximum_possible_score": 0.0,
            }

        found = False
        for i, eval_item in enumerate(review_data["criteria_evaluations"]):
            if eval_item.get("criteria_index") == criteria_index + 1:
                review_data["criteria_evaluations"][i] = evaluation
                found = True
                break

        if not found:
            review_data["criteria_evaluations"].append(evaluation)

        overall_score = sum(e.get("awarded_score", 0) for e in review_data["criteria_evaluations"])
        max_score = sum(c.get("nota_maxima", 0) for c in criteria_list)

        review_data["overall_score"] = overall_score
        review_data["maximum_possible_score"] = max_score

        with open(review_file, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

        return review_data

    def run_all_reviews(self, criteria_file: str) -> int:
        exam_files = [f for f in os.listdir(self.exams_dir) if f.endswith(".c")]
        count = 0

        for exam_file in exam_files:
            try:
                self.run_single_review(exam_file, criteria_file)
                count += 1
            except Exception as e:
                logger.error(f"Failed to review {exam_file}: {e}")

        return count
