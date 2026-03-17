import json
import logging
import os
from typing import Any, Dict

from config import DEFAULT_MODEL, OPENROUTER_API_KEY

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

    def load_criteria(self, criteria_file: str) -> Dict:
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
        criteria = self.load_criteria(criteria_file)

        prompt = self.create_prompt(exam_content, criteria)

        try:
            ai_response = self.api_client.call_api(prompt)
            evaluation = self.api_client.parse_ai_response(ai_response)
        except Exception as e:
            logger.error(f"Evaluation failed for criteria {criteria_file}: {e}")
            evaluation = {
                "criteria_title": criteria.get("titulo", ""),
                "criteria_description": criteria.get("descripcion", ""),
                "maximum_score": criteria.get("nota_maxima", 0),
                "awarded_score": 0,
                "justification": f"Error: {str(e)}",
                "subsection_evaluations": [],
            }

        evaluation["criteria_filename"] = criteria_file
        evaluation["criteria_title"] = criteria.get("titulo", "")

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
                "total_criteria": 0,
                "criteria_evaluations": [],
                "overall_score": 0.0,
                "maximum_possible_score": 0.0,
            }

        found = False
        for i, eval_item in enumerate(review_data["criteria_evaluations"]):
            if eval_item.get("criteria_filename") == criteria_file:
                review_data["criteria_evaluations"][i] = evaluation
                found = True
                break

        if not found:
            review_data["criteria_evaluations"].append(evaluation)

        overall_score = sum(e.get("awarded_score", 0) for e in review_data["criteria_evaluations"])

        all_criteria_files = [f for f in os.listdir(self.criteria_dir) if f.endswith(".json")]
        max_score = 0.0
        for cf in all_criteria_files:
            try:
                c = self.load_criteria(cf)
                max_score += c.get("nota_maxima", 0)
            except Exception:
                pass

        review_data["overall_score"] = overall_score
        review_data["maximum_possible_score"] = max_score

        with open(review_file, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)

        return review_data

    def run_single_criteria_review(self, exam_file: str, criteria_file: str) -> Dict:
        return self.run_single_review(exam_file, criteria_file)

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

    def run_all_criteria_reviews(self) -> int:
        exam_files = [f for f in os.listdir(self.exams_dir) if f.endswith(".c")]
        criteria_files = [f for f in os.listdir(self.criteria_dir) if f.endswith(".json")]

        count = 0
        for exam_file in exam_files:
            for criteria_file in criteria_files:
                try:
                    self.run_single_review(exam_file, criteria_file)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to review {exam_file} with {criteria_file}: {e}")

        return count

    def generate_annotation(self, exam_file: str, annotated_exams_dir: str) -> str:  # noqa: E501
        exam_content = self.load_exam(exam_file)

        prompt = (
            "You are a C programming teacher reviewing a student's exam submission.\n"
            "Analyze the code and add comments starting with //REVIEWER: to indicate errors, bugs, problems, or mistakes.\n"
            "\n"
            "IMPORTANT:\n"
            "- Only add comments, do NOT modify the code itself\n"
            "- Add comments on the SAME LINE after the code, or on the line before if at the start of a block\n"
            "- Use exactly //REVIEWER: as the prefix for your comments\n"
            "- Focus on: syntax errors, logic errors, bugs, style issues, missing error handling, memory issues\n"
            "- If no issues found, add a single comment //REVIEWER: Code looks good, no issues found\n"
            "\n"
            "Original code:\n"
            "```c\n" + exam_content + "\n```\n"
            "\n"
            "Return ONLY the annotated C code with your //REVIEWER: comments, no other text."
        )

        try:
            ai_response = self.api_client.call_api(prompt)
            annotated_content = self._clean_annotation_response(ai_response)
        except Exception as e:
            logger.error(f"Annotation failed for {exam_file}: {e}")
            annotated_content = f"//REVIEWER: Error generating annotation: {str(e)}\n{exam_content}"

        base_name = os.path.splitext(exam_file)[0]
        annotated_filename = f"{base_name}_annotated.c"
        annotated_path = os.path.join(annotated_exams_dir, annotated_filename)

        with open(annotated_path, "w", encoding="utf-8") as f:
            f.write(annotated_content)

        return annotated_filename

    def _clean_annotation_response(self, response: str) -> str:
        cleaned = response.strip()
        if cleaned.startswith("```c"):
            cleaned = cleaned[4:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.startswith("```c"):
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
