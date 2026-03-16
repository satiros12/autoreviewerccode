#!/usr/bin/env python3
"""
Exam Reviewer - AI-powered exam evaluation system
Reads C exam files and evaluates them using OpenRouter AI API
"""

import os
import json
import time
import logging
from typing import Dict, List, Any
import requests

# IMPORTANT: Replace with your actual OpenRouter API key
# You should get this from https://openrouter.ai/
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
# Configuration
EXAMS_DIR = "ExamsTest"
CRITERIA_FILE = "evaluation_improved.json"
OUTPUT_DIR = "JSON_REVIEWS"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExamReviewer:
    def __init__(self, api_key: str):
        """
        Initialize the ExamReviewer with OpenRouter API key

        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-chat"

        # Headers for OpenRouter API
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cexams.local",  # Optional
            "X-Title": "CExams AI Reviewer",  # Optional
        }

    def load_criteria(self, criteria_file: str) -> List[Dict]:
        """
        Load evaluation criteria from JSON file

        Args:
            criteria_file: Path to evaluation_improved.json

        Returns:
            List of criteria dictionaries
        """
        try:
            with open(criteria_file, "r", encoding="utf-8") as f:
                criteria = json.load(f)
            logger.info(f"Loaded {len(criteria)} criteria from {criteria_file}")
            return criteria
        except Exception as e:
            logger.error(f"Error loading criteria: {e}")
            raise

    def read_exam_file(self, file_path: str) -> str:
        """
        Read exam file content

        Args:
            file_path: Path to exam file

        Returns:
            File content as string
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Read exam file: {file_path} ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error reading exam file {file_path}: {e}")
            raise

    def create_prompt(self, exam_content: str, criteria: Dict) -> str:
        """
        Create prompt for AI evaluation based on criteria

        Args:
            exam_content: C code content
            criteria: Single criteria dictionary

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are evaluating a C programming exam submission based on specific criteria.

EXAM CODE:
```c
{exam_content}
```

CRITERIA TO EVALUATE:
Title: {criteria.get("titulo", "N/A")}
Description: {criteria.get("descripcion", "N/A")}
Maximum Score: {criteria.get("nota_maxima", "N/A")}

Subsections:
"""

        # Add subsections
        for i, sub in enumerate(criteria.get("subapartados", []), 1):
            prompt += (
                f"\n{i}. {sub.get('nombre', 'N/A')}: {sub.get('descripcion', 'N/A')}"
            )
            prompt += f" (Points: {sub.get('puntos', 'N/A')})"
            if sub.get("anulador", False):
                prompt += " [NULLIFIER - Can void entire criteria]"

        prompt += """

INSTRUCTIONS:
1. Analyze the C code against each subsection above
2. For each subsection, determine if it's implemented correctly
3. Assign points based on the specified point values
4. If a NULLIFIER subsection applies, the entire criteria may get 0 points
5. Provide a clear justification for your evaluation

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{
    "criteria_title": "string",
    "criteria_description": "string",
    "maximum_score": number,
    "awarded_score": number,
    "justification": "string explaining the score",
    "subsection_evaluations": [
        {
            "subsection_name": "string",
            "subsection_description": "string",
            "possible_points": number,
            "awarded_points": number,
            "reasoning": "string explaining the points"
        }
    ]
}

IMPORTANT: Return ONLY valid JSON, no other text."""

        return prompt

    def call_ai_api(self, prompt: str) -> str:
        """
        Call OpenRouter AI API

        Args:
            prompt: The prompt to send to AI

        Returns:
            AI response text
        """
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert C programming evaluator. Analyze code and provide detailed evaluations in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2000,
        }

        try:
            logger.info("Calling OpenRouter AI API...")
            response = requests.post(
                self.base_url, headers=self.headers, json=data, timeout=60
            )
            response.raise_for_status()

            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            logger.info("AI API call successful")

            return ai_response

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in AI API call: {e}")
            raise

    def parse_ai_response(self, response_text: str) -> Dict:
        """
        Parse AI response JSON

        Args:
            response_text: AI response text

        Returns:
            Parsed JSON as dictionary
        """
        try:
            # Clean the response - sometimes AI adds markdown code blocks
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            raise

    def review_exam(self, exam_path: str, criteria_list: List[Dict]) -> Dict:
        """
        Review a single exam file against all criteria

        Args:
            exam_path: Path to exam file
            criteria_list: List of criteria dictionaries

        Returns:
            Dictionary with review results
        """
        exam_name = os.path.splitext(os.path.basename(exam_path))[0]
        logger.info(f"Starting review for: {exam_name}")

        try:
            # Read exam content
            exam_content = self.read_exam_file(exam_path)

            results = {
                "exam_name": exam_name,
                "exam_file": os.path.basename(exam_path),
                "total_criteria": len(criteria_list),
                "criteria_evaluations": [],
                "overall_score": 0,
                "maximum_possible_score": 0,
            }

            # Process each criteria
            for i, criteria in enumerate(criteria_list, 1):
                logger.info(
                    f"Evaluating criteria {i}/{len(criteria_list)}: {criteria.get('titulo', 'Unknown')}"
                )

                try:
                    # Create prompt
                    prompt = self.create_prompt(exam_content, criteria)

                    # Call AI API
                    ai_response = self.call_ai_api(prompt)

                    # Parse response
                    evaluation = self.parse_ai_response(ai_response)

                    # Add criteria info to evaluation
                    evaluation["criteria_index"] = i

                    # Add to results
                    results["criteria_evaluations"].append(evaluation)

                    # Update overall scores
                    results["overall_score"] += evaluation.get("awarded_score", 0)
                    results["maximum_possible_score"] += criteria.get("nota_maxima", 0)

                    # Add delay to avoid rate limiting
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error evaluating criteria {i}: {e}")
                    error_eval = {
                        "criteria_index": i,
                        "criteria_title": criteria.get("titulo", "Unknown"),
                        "error": str(e),
                        "awarded_score": 0,
                    }
                    results["criteria_evaluations"].append(error_eval)
                    results["maximum_possible_score"] += criteria.get("nota_maxima", 0)
                    # Continue with next criteria

            logger.info(
                f"Completed review for {exam_name}. Score: {results['overall_score']}/{results['maximum_possible_score']}"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to review exam {exam_path}: {e}")
            raise

    def save_results(self, results: Dict, output_dir: str = "JSON_REVIEWS"):
        """
        Save review results to JSON file

        Args:
            results: Review results dictionary
            output_dir: Directory to save results
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Create filename
            exam_name = results["exam_name"]
            filename = f"{exam_name}_review.json"
            filepath = os.path.join(output_dir, filename)

            # Save to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved review results to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise


def main():
    """
    Main function to run the exam reviewer
    """
    print("CExams AI Reviewer")
    print("=" * 50)
    

    if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY_HERE":
        print("\nERROR: Please update the OPENROUTER_API_KEY in the script!")
        print("Get your API key from: https://openrouter.ai/")
        print("Then edit the 'OPENROUTER_API_KEY' variable in exam_reviewer.py")
        return

    # Initialize reviewer
    reviewer = ExamReviewer(OPENROUTER_API_KEY)

    try:
        # Load criteria
        print(f"Loading criteria from {CRITERIA_FILE}...")
        criteria_list = reviewer.load_criteria(CRITERIA_FILE)

        # Get exam files
        print(f"Scanning exam files in {EXAMS_DIR}...")
        exam_files = []
        for file in os.listdir(EXAMS_DIR):
            if file.endswith(".c"):
                exam_files.append(os.path.join(EXAMS_DIR, file))

        if not exam_files:
            print(f"No exam files found in {EXAMS_DIR}")
            return

        print(f"Found {len(exam_files)} exam files to review")

        # Process each exam
        for i, exam_file in enumerate(exam_files, 1):
            print(f"\n{'=' * 50}")
            print(
                f"Reviewing exam {i}/{len(exam_files)}: {os.path.basename(exam_file)}"
            )
            print(f"{'=' * 50}")

            try:
                # Review exam
                results = reviewer.review_exam(exam_file, criteria_list)

                # Save results
                output_path = reviewer.save_results(results, OUTPUT_DIR)

                # Print summary
                print(f"✓ Review completed: {results['exam_name']}")
                print(
                    f"  Score: {results['overall_score']:.2f}/{results['maximum_possible_score']:.2f}"
                )
                print(f"  Results saved to: {output_path}")

            except Exception as e:
                print(f"✗ Failed to review {exam_file}: {e}")
                continue

        print(f"\n{'=' * 50}")
        print("All exams reviewed successfully!")
        print(f"Results saved in: {OUTPUT_DIR}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
