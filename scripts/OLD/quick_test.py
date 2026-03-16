#!/usr/bin/env python3
"""
Quick test of the main exam_reviewer script
"""

import os
import sys

# Run the actual script with modified parameters
os.environ["TEST_MODE"] = "true"

# Import and run the main script
import exam_reviewer

# Monkey patch to limit the scope
original_main = exam_reviewer.main


def limited_main():
    """Limited version for testing"""
    print("QUICK TEST MODE - Processing 1 exam with 2 criteria")
    print("=" * 60)

    # Get the reviewer
    reviewer = exam_reviewer.ExamReviewer(os.environ["OPENROUTER_API_KEY"])

    try:
        # Load criteria
        criteria_list = reviewer.load_criteria(exam_reviewer.CRITERIA_FILE)

        # LIMIT: Use only first 2 criteria
        test_criteria = criteria_list[:2]
        print(f"Using {len(test_criteria)} criteria (out of {len(criteria_list)})")

        # Get exam files
        exam_files = []
        for file in os.listdir(exam_reviewer.EXAMS_DIR):
            if file.endswith(".c"):
                exam_files.append(os.path.join(exam_reviewer.EXAMS_DIR, file))

        if not exam_files:
            print(f"No exam files found in {exam_reviewer.EXAMS_DIR}")
            return

        # LIMIT: Use only first exam
        test_exam = exam_files[0]
        exam_name = os.path.basename(test_exam)
        print(f"\nProcessing: {exam_name}")
        print("-" * 40)

        # Review exam
        results = reviewer.review_exam(test_exam, test_criteria)

        # Save results
        output_path = reviewer.save_results(results, exam_reviewer.OUTPUT_DIR)

        # Summary
        print(f"\n✓ REVIEW COMPLETE")
        print(f"  Exam: {results['exam_name']}")
        print(
            f"  Score: {results['overall_score']:.2f}/{results['maximum_possible_score']:.2f}"
        )
        print(f"  File: {output_path}")

        # Show criteria breakdown
        print(f"\nCriteria Breakdown:")
        for i, eval in enumerate(results["criteria_evaluations"], 1):
            title = eval.get("criteria_title", f"Criteria {i}")
            score = eval.get("awarded_score", 0)
            max_score = eval.get("maximum_score", 0)
            print(f"  {i}. {title[:50]}...: {score}/{max_score}")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Replace main with limited version
    exam_reviewer.main = limited_main

    # Run the limited version
    success = limited_main()

    if success:
        print(f"\n{'=' * 60}")
        print("Quick test successful! The full script is ready to run.")
        print("\nTo run full review of all exams:")
        print("  python exam_reviewer.py")
        print("\nNote: Full review will process 10 exams × 7 criteria = 70 API calls")
        print("Estimated time: ~30-40 minutes")
        print("Estimated cost: < $0.50")
    else:
        print(f"\n{'=' * 60}")
        print("Test failed. Please check the error above.")
