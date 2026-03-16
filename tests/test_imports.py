#!/usr/bin/env python3
"""
Test imports for modular CExams package
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_imports():
    """Test all module imports"""
    print("Testing CExams package imports...")

    try:
        # Test model imports
        from src.cexams.models.criteria import (
            Subsection,
            Criteria,
            SubsectionEvaluation,
            CriteriaEvaluation,
            ExamReview,
        )

        print("✓ Models imported successfully")

        # Test API imports
        from src.cexams.api.client import OpenRouterClient

        print("✓ API client imported successfully")

        # Test core imports
        from src.cexams.core.reviewer import (
            CriteriaLoader,
            PromptGenerator,
            ExamReviewer,
        )

        print("✓ Core modules imported successfully")

        # Test main module
        from src.cexams.__main__ import main

        print("✓ Main module imported successfully")

        print("\nAll imports successful! Package structure is correct.")
        return True

    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
