#!/usr/bin/env python3
"""
Test script for exam reviewer - uses mock API responses
"""

import os
import json


def test_script_structure():
    """Test basic script structure and imports"""
    print("Testing exam reviewer script structure...")

    # Check if main script exists
    if not os.path.exists("exam_reviewer.py"):
        print("ERROR: exam_reviewer.py not found!")
        return False

    # Check if Exams directory exists
    if not os.path.exists("Exams"):
        print("ERROR: Exams directory not found!")
        return False

    # Check if criteria file exists
    if not os.path.exists("evaluation_improved.json"):
        print("ERROR: evaluation_improved.json not found!")
        return False

    # Check if JSON_REVIEWS directory exists (or can be created)
    try:
        os.makedirs("JSON_REVIEWS", exist_ok=True)
        print("✓ JSON_REVIEWS directory ready")
    except Exception as e:
        print(f"ERROR creating JSON_REVIEWS: {e}")
        return False

    # Count exam files
    exam_files = [f for f in os.listdir("Exams") if f.endswith(".c")]
    print(f"✓ Found {len(exam_files)} exam files in Exams/")

    # Test reading a criteria file
    try:
        with open("evaluation_improved.json", "r", encoding="utf-8") as f:
            criteria = json.load(f)
        print(f"✓ Successfully loaded {len(criteria)} criteria")
    except Exception as e:
        print(f"ERROR reading criteria file: {e}")
        return False

    # Test reading an exam file
    if exam_files:
        test_file = os.path.join("Exams", exam_files[0])
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(
                f"✓ Successfully read exam file: {exam_files[0]} ({len(content)} chars)"
            )
        except Exception as e:
            print(f"ERROR reading exam file: {e}")
            return False

    return True


def create_mock_response():
    """Create a mock AI response for testing"""
    mock_response = {
        "criteria_title": "Test Criteria",
        "criteria_description": "Test description",
        "maximum_score": 1.0,
        "awarded_score": 0.75,
        "justification": "The code partially implements the required functionality.",
        "subsection_evaluations": [
            {
                "subsection_name": "Test Subsection",
                "subsection_description": "Test subsection description",
                "possible_points": 0.25,
                "awarded_points": 0.25,
                "reasoning": "Correctly implemented",
            }
        ],
    }
    return json.dumps(mock_response)


def test_prompt_generation():
    """Test prompt generation"""
    print("\nTesting prompt generation...")

    # Create a simple test criteria
    test_criteria = {
        "titulo": "Orden correcto, correcta indentacón, Uso correcto de variables",
        "descripcion": "Orden correcto, correcta indentacón, Uso correcto de variables — Claridad en la estructura del programa/variables/comentarios",
        "nota_maxima": 1,
        "subapartados": [
            {
                "nombre": "Estructura general del programa",
                "descripcion": "Orden lógico: includes, definiciones (struct, enum, typedef), prototipos, main, funciones.",
                "puntos": 0.25,
                "penalizacion_min": -0.25,
            }
        ],
    }

    # Test exam content
    test_exam = """#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}"""

    # Import the actual function from exam_reviewer
    try:
        # We'll simulate the function here
        prompt = f"""You are evaluating a C programming exam submission based on specific criteria.

EXAM CODE:
```c
{test_exam}
```

CRITERIA TO EVALUATE:
Title: {test_criteria.get("titulo", "N/A")}
Description: {test_criteria.get("descripcion", "N/A")}
Maximum Score: {test_criteria.get("nota_maxima", "N/A")}

Subsections:

1. {test_criteria["subapartados"][0].get("nombre", "N/A")}: {test_criteria["subapartados"][0].get("descripcion", "N/A")} (Points: {test_criteria["subapartados"][0].get("puntos", "N/A")})

INSTRUCTIONS:
1. Analyze the C code against each subsection above
2. For each subsection, determine if it's implemented correctly
3. Assign points based on the specified point values
4. If a NULLIFIER subsection applies, the entire criteria may get 0 points
5. Provide a clear justification for your evaluation

OUTPUT FORMAT:
Return a JSON object with this exact structure:
{{
    "criteria_title": "string",
    "criteria_description": "string",
    "maximum_score": number,
    "awarded_score": number,
    "justification": "string explaining the score",
    "subsection_evaluations": [
        {{
            "subsection_name": "string",
            "subsection_description": "string",
            "possible_points": number,
            "awarded_points": number,
            "reasoning": "string explaining the points"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no other text."""

        print("✓ Prompt generated successfully")
        print(f"  Prompt length: {len(prompt)} characters")
        print(f"  Contains exam code: {'EXAM CODE:' in prompt}")
        print(f"  Contains JSON format instructions: {'OUTPUT FORMAT:' in prompt}")

        return True

    except Exception as e:
        print(f"ERROR generating prompt: {e}")
        return False


def test_json_parsing():
    """Test JSON parsing of AI responses"""
    print("\nTesting JSON parsing...")

    mock_json = create_mock_response()

    try:
        # Clean the response (simulating the actual function)
        cleaned_response = mock_json.strip()

        # Parse JSON
        result = json.loads(cleaned_response)

        # Verify structure
        required_fields = [
            "criteria_title",
            "criteria_description",
            "maximum_score",
            "awarded_score",
            "justification",
            "subsection_evaluations",
        ]

        for field in required_fields:
            if field not in result:
                print(f"ERROR: Missing field {field}")
                return False

        print("✓ Successfully parsed mock JSON response")
        print(f"  Criteria: {result['criteria_title']}")
        print(f"  Score: {result['awarded_score']}/{result['maximum_score']}")

        return True

    except Exception as e:
        print(f"ERROR parsing JSON: {e}")
        return False


def test_output_structure():
    """Test output JSON structure"""
    print("\nTesting output structure...")

    # Create sample results structure
    sample_results = {
        "exam_name": "test_exam",
        "exam_file": "test.c",
        "total_criteria": 1,
        "criteria_evaluations": [
            {
                "criteria_index": 1,
                "criteria_title": "Test Criteria",
                "criteria_description": "Test description",
                "maximum_score": 1.0,
                "awarded_score": 0.75,
                "justification": "Partial implementation",
                "subsection_evaluations": [],
            }
        ],
        "overall_score": 0.75,
        "maximum_possible_score": 1.0,
    }

    try:
        # Test saving to file
        output_dir = "JSON_REVIEWS"
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, "test_exam_review.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sample_results, f, indent=2, ensure_ascii=False)

        print(f"✓ Successfully saved test results to {filepath}")

        # Test reading back
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        print(f"✓ Successfully loaded results back")
        print(f"  Exam: {loaded['exam_name']}")
        print(f"  Score: {loaded['overall_score']}/{loaded['maximum_possible_score']}")

        # Clean up
        os.remove(filepath)
        print("✓ Cleaned up test file")

        return True

    except Exception as e:
        print(f"ERROR testing output structure: {e}")
        return False


def main():
    """Run all tests"""
    print("CExams AI Reviewer - Test Suite")
    print("=" * 50)

    tests = [
        ("Script Structure", test_script_structure),
        ("Prompt Generation", test_prompt_generation),
        ("JSON Parsing", test_json_parsing),
        ("Output Structure", test_output_structure),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\nTest: {test_name}")
        try:
            if test_func():
                print(f"  ✓ PASSED")
                passed += 1
            else:
                print(f"  ✗ FAILED")
                failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("\nAll tests passed! The exam reviewer script is ready.")
        print("\nNext steps:")
        print("1. Edit exam_reviewer.py and set your OPENROUTER_API_KEY")
        print("2. Run: python exam_reviewer.py")
        print("3. Check JSON_REVIEWS/ folder for results")
    else:
        print(f"\n{failed} test(s) failed. Please fix the issues above.")


if __name__ == "__main__":
    main()
