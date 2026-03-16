"""
Main entry point for CExams package
"""

import os
import sys
import logging
import argparse
from pathlib import Path

from .core.reviewer import ExamReviewer, CriteriaLoader


def configure_logging(verbose: bool = False):
    """Configure logging settings"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
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


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog="cexams",
        description="CExams - AI-powered C programming exam evaluation system",
    )
    parser.add_argument(
        "--exams-dir",
        type=str,
        default="Exams",
        help="Directory containing exam files (default: Exams)",
    )
    parser.add_argument(
        "--criteria-file",
        type=str,
        default="criteria/evaluation_improved.json",
        help="Path to evaluation criteria JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reviews",
        help="Directory to save review results (default: reviews)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (single exam, single criteria)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek/deepseek-chat",
        help="AI model to use for evaluation",
    )
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()

    print("CExams AI Reviewer")
    print("=" * 50)

    try:
        # Get API key
        api_key = get_api_key()

        # Configure logging
        configure_logging(args.verbose)

        # Initialize components
        reviewer = ExamReviewer(api_key, model=args.model)
        criteria_loader = CriteriaLoader()

        # Load criteria
        print(f"Loading criteria from {args.criteria_file}...")
        criteria_list = criteria_loader.load_criteria(args.criteria_file)

        # Check for test mode
        if args.test_mode:
            criteria_list = criteria_list[:1]
            print(f"TEST MODE: Using only first criteria")

        # Get exam files
        print(f"Scanning exam files in {args.exams_dir}...")
        if not os.path.isdir(args.exams_dir):
            print(f"ERROR: Exams directory not found: {args.exams_dir}")
            return

        exam_files = sorted(
            [
                os.path.join(args.exams_dir, f)
                for f in os.listdir(args.exams_dir)
                if f.endswith(".c")
            ]
        )

        if not exam_files:
            print(f"No exam files found in {args.exams_dir}")
            return

        if args.test_mode:
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
                output_path = reviewer.save_review(review, args.output_dir)

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
        if args.test_mode:
            print("TEST COMPLETE! Script is working correctly.")
            print("To run full review, remove --test-mode flag")
        else:
            print("All exams reviewed successfully!")
        print(f"Results saved in: {args.output_dir}")

    except ValueError as e:
        print(f"\nERROR: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
