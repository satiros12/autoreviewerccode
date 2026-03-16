"""
Main entry point for CExams package
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .core.reviewer import ExamReviewer, CriteriaLoader


def configure_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def get_api_key():
    """Get OpenRouter API key from environment or config"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == "YOUR_OPENROUTER_API_KEY_HERE":
        raise ValueError(
            "OPENROUTER_API_KEY environment variable not set or invalid.\n"
            "Set it with: export OPENROUTER_API_KEY='your-key-here'\n"
            "Get your API key from: https://openrouter.ai/"
        )
    return api_key


def main():
    """Main function"""
    print("CExams AI Reviewer")
    print("=" * 50)

    # Configuration
    EXAMS_DIR = "Exams"
    CRITERIA_FILE = "criteria/evaluation_improved.json"
    OUTPUT_DIR = "reviews"

    try:
        # Get API key
        api_key = get_api_key()

        # Initialize components
        configure_logging()
        reviewer = ExamReviewer(api_key)
        criteria_loader = CriteriaLoader()

        # Load criteria
        print(f"Loading criteria from {CRITERIA_FILE}...")
        criteria_list = criteria_loader.load_criteria(CRITERIA_FILE)

        # Check for test mode
        TEST_MODE = os.environ.get("TEST_MODE") == "true"
        if TEST_MODE:
            criteria_list = criteria_list[:1]
            print(f"TEST MODE: Using only first criteria")

        # Get exam files
        print(f"Scanning exam files in {EXAMS_DIR}...")
        exam_files = []
        for file in os.listdir(EXAMS_DIR):
            if file.endswith(".c"):
                exam_files.append(os.path.join(EXAMS_DIR, file))

        if not exam_files:
            print(f"No exam files found in {EXAMS_DIR}")
            return

        if TEST_MODE:
            exam_files = exam_files[:1]
            print(f"TEST MODE: Using only first exam")

        print(f"Found {len(exam_files)} exam files to review")

        # Process each exam
        for i, exam_file in enumerate(exam_files, 1):
            print(f"\n{'=' * 50}")
            print(f"Reviewing exam {i}/{len(exam_files)}: {Path(exam_file).name}")
            print(f"{'=' * 50}")

            try:
                # Review exam
                review = reviewer.review_exam(exam_file, criteria_list)

                # Save results
                output_path = reviewer.save_review(review, OUTPUT_DIR)

                # Print summary
                print(f"✓ Review completed: {review.exam_name}")
                print(
                    f"  Score: {review.overall_score:.2f}/{review.maximum_possible_score:.2f}"
                )
                print(f"  Results saved to: {output_path}")

            except Exception as e:
                print(f"✗ Failed to review {exam_file}: {e}")
                continue

        print(f"\n{'=' * 50}")
        if TEST_MODE:
            print("TEST COMPLETE! Script is working correctly.")
            print("To run full review, remove TEST_MODE environment variable")
        else:
            print("All exams reviewed successfully!")
        print(f"Results saved in: {OUTPUT_DIR}")

    except ValueError as e:
        print(f"\nERROR: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
