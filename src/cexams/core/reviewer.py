"""
Core exam review functionality
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from ..api.client import OpenRouterClient
from ..models.criteria import Criteria, CriteriaEvaluation, ExamReview

logger = logging.getLogger(__name__)


class CriteriaLoader:
    """Handles loading and parsing evaluation criteria"""

    @staticmethod
    def load_criteria(file_path: str) -> List[Criteria]:
        """
        Load evaluation criteria from JSON file

        Args:
            file_path: Path to criteria JSON file

        Returns:
            List of Criteria objects
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                criteria_data = json.load(f)

            criteria_list = []
            for criteria_dict in criteria_data:
                criteria = Criteria.from_dict(criteria_dict)
                criteria_list.append(criteria)

            logger.info(f"Loaded {len(criteria_list)} criteria from {file_path}")
            return criteria_list

        except Exception as e:
            logger.error(f"Error loading criteria: {e}")
            raise

    @staticmethod
    def read_exam_file(file_path: str) -> str:
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


class PromptGenerator:
    """Generates prompts for AI evaluation"""

    @staticmethod
    def create_prompt(exam_content: str, criteria: Criteria) -> str:
        """
        Create prompt for AI evaluation based on criteria

        Args:
            exam_content: C code content
            criteria: Criteria object

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are evaluating a C programming exam submission based on specific criteria.

EXAM CODE:
```c
{exam_content}
```

CRITERIA TO EVALUATE:
Title: {criteria.titulo}
Description: {criteria.descripcion}
Maximum Score: {criteria.nota_maxima}

Subsections:
"""

        # Add subsections
        for i, sub in enumerate(criteria.subapartados, 1):
            prompt += f"\n{i}. {sub.nombre}: {sub.descripcion}"
            prompt += f" (Points: {sub.puntos})"
            if sub.anulador:
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


class ExamReviewer:
    """Main exam reviewer class"""

    def __init__(self, api_key: str, model: str = "deepseek/deepseek-chat"):
        """
        Initialize ExamReviewer

        Args:
            api_key: OpenRouter API key
            model: AI model to use for evaluation
        """
        self.api_client = OpenRouterClient(api_key, model=model)
        self.criteria_loader = CriteriaLoader()
        self.prompt_generator = PromptGenerator()

    def review_exam(self, exam_path: str, criteria_list: List[Criteria]) -> ExamReview:
        """
        Review a single exam file against all criteria

        Args:
            exam_path: Path to exam file
            criteria_list: List of Criteria objects

        Returns:
            ExamReview object with results
        """
        exam_name = Path(exam_path).stem
        exam_file = Path(exam_path).name
        logger.info(f"Starting review for: {exam_name}")

        try:
            # Read exam content
            exam_content = self.criteria_loader.read_exam_file(exam_path)

            # Initialize review
            review = ExamReview(
                exam_name=exam_name,
                exam_file=exam_file,
                total_criteria=len(criteria_list),
            )

            # Process each criteria
            for i, criteria in enumerate(criteria_list, 1):
                logger.info(f"Evaluating criteria {i}/{len(criteria_list)}: {criteria.titulo}")

                try:
                    # Create prompt
                    prompt = self.prompt_generator.create_prompt(exam_content, criteria)

                    # Call AI API
                    ai_response = self.api_client.call_api(prompt)

                    # Parse response
                    evaluation_dict = self.api_client.parse_ai_response(ai_response)

                    # Create CriteriaEvaluation object
                    evaluation = self._create_criteria_evaluation(evaluation_dict, i)

                    # Add to review
                    review.criteria_evaluations.append(evaluation)

                    # Update overall scores
                    review.overall_score += evaluation.awarded_score
                    review.maximum_possible_score += criteria.nota_maxima

                    # Add delay to avoid rate limiting
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error evaluating criteria {i}: {e}")
                    # Create error evaluation
                    error_eval = CriteriaEvaluation(
                        criteria_title=criteria.titulo,
                        criteria_description=criteria.descripcion,
                        maximum_score=criteria.nota_maxima,
                        awarded_score=0.0,
                        justification=f"Error during evaluation: {str(e)[:100]}",
                        criteria_index=i,
                    )
                    review.criteria_evaluations.append(error_eval)
                    review.maximum_possible_score += criteria.nota_maxima
                    # Continue with next criteria

            logger.info(
                f"Completed review for {exam_name}. "
                f"Score: {review.overall_score}/{review.maximum_possible_score}"
            )
            return review

        except Exception as e:
            logger.error(f"Failed to review exam {exam_path}: {e}")
            raise

    def _create_criteria_evaluation(
        self, eval_dict: Dict[str, Any], index: int
    ) -> CriteriaEvaluation:
        """Create CriteriaEvaluation from parsed dictionary"""
        from ..models.criteria import SubsectionEvaluation

        subsection_evals = []
        for sub_eval in eval_dict.get("subsection_evaluations", []):
            subsection_eval = SubsectionEvaluation(
                subsection_name=sub_eval.get("subsection_name", ""),
                subsection_description=sub_eval.get("subsection_description", ""),
                possible_points=sub_eval.get("possible_points", 0.0),
                awarded_points=sub_eval.get("awarded_points", 0.0),
                reasoning=sub_eval.get("reasoning", ""),
            )
            subsection_evals.append(subsection_eval)

        return CriteriaEvaluation(
            criteria_title=eval_dict.get("criteria_title", ""),
            criteria_description=eval_dict.get("criteria_description", ""),
            maximum_score=eval_dict.get("maximum_score", 0.0),
            awarded_score=eval_dict.get("awarded_score", 0.0),
            justification=eval_dict.get("justification", ""),
            subsection_evaluations=subsection_evals,
            criteria_index=index,
        )

    def save_review(self, review: ExamReview, output_dir: str = "reviews") -> str:
        """
        Save review results to JSON file

        Args:
            review: ExamReview object
            output_dir: Directory to save results

        Returns:
            Path to saved file
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Create filename
            filename = f"{review.exam_name}_review.json"
            filepath = os.path.join(output_dir, filename)

            # Convert to dict and save
            review_dict = review.to_dict()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(review_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved review results to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
