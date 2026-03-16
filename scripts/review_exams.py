#!/usr/bin/env python3
"""
Simple CLI script to review exams using the modular CExams package
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cexams.__main__ import main

if __name__ == "__main__":
    main()
