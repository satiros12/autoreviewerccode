#!/usr/bin/env python3
"""
Test single exam review with one criteria
"""

import os
import json
import time
import requests

# Get API key from environment
API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    print("ERROR: OPENROUTER_API_KEY environment variable not set")
    exit(1)


class SimpleReviewer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cexams.local",
            "X-Title": "CExams Test",
        }

    def read_exam(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def create_prompt(self, exam_content, criteria):
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
4. Provide a clear justification for your evaluation

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

    def call_ai(self, prompt):
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert C programming evaluator. Analyze code and provide detailed evaluations in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=self.headers,
            json=data,
            timeout=60,
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def parse_response(self, response_text):
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        return json.loads(cleaned)


def main():
    print("Testing Single Exam Review")
    print("=" * 50)

    # Initialize reviewer
    reviewer = SimpleReviewer(API_KEY)

    # Load just one criteria
    try:
        with open("evaluation_improved.json", "r", encoding="utf-8") as f:
            all_criteria = json.load(f)

        # Use first criteria only
        test_criteria = all_criteria[0]
        print(f"Using criteria: {test_criteria.get('titulo', 'Unknown')}")
        print(f"Maximum score: {test_criteria.get('nota_maxima', 'N/A')}")
        print(f"Subsections: {len(test_criteria.get('subapartados', []))}")
    except Exception as e:
        print(f"Error loading criteria: {e}")
        return

    # Get first exam file
    exam_files = [f for f in os.listdir("Exams") if f.endswith(".c")]
    if not exam_files:
        print("No exam files found")
        return

    test_exam = os.path.join("Exams", exam_files[0])
    print(f"\nTesting with exam: {exam_files[0]}")

    try:
        # Read exam
        exam_content = reviewer.read_exam(test_exam)
        print(f"Exam length: {len(exam_content)} characters")

        # Create prompt
        print("\nCreating prompt...")
        prompt = reviewer.create_prompt(exam_content, test_criteria)
        print(f"Prompt length: {len(prompt)} characters")
        print(f"First 200 chars:\n{prompt[:200]}...")

        # Call AI
        print("\nCalling AI API...")
        start_time = time.time()
        ai_response = reviewer.call_ai(prompt)
        elapsed = time.time() - start_time
        print(f"AI call completed in {elapsed:.2f} seconds")
        print(f"Response length: {len(ai_response)} characters")
        print(f"Response preview:\n{ai_response[:200]}...")

        # Parse response
        print("\nParsing JSON response...")
        result = reviewer.parse_response(ai_response)

        print("\n✓ Review Successful!")
        print(f"Criteria: {result.get('criteria_title', 'N/A')}")
        print(
            f"Awarded Score: {result.get('awarded_score', 'N/A')}/{result.get('maximum_score', 'N/A')}"
        )
        print(f"Justification: {result.get('justification', 'N/A')[:100]}...")

        # Save result
        output = {
            "exam_name": os.path.splitext(exam_files[0])[0],
            "exam_file": exam_files[0],
            "criteria_evaluation": result,
        }

        os.makedirs("JSON_REVIEWS", exist_ok=True)
        output_file = os.path.join("JSON_REVIEWS", "test_single_review.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_file}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
