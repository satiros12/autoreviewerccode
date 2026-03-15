import click
import json
from pathlib import Path
from typing import Optional
import sys

from .rubric_generator import RubricGenerator
from .exam_analyzer import ExamEvaluator, CCodeAnalyzer


@click.group()
def main():
    """C Exam Grader - Automatic C exam evaluation and grading system"""
    pass


@main.command()
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(exists=True),
    default="evaluation_criteria.csv",
    help="Path to evaluation criteria CSV file",
)
@click.option(
    "--name", "rubric_name", default="Exam Rubric", help="Name for the generated rubric"
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(),
    default="generated_rubric.json",
    help="Output JSON file path",
)
def generate_rubric(csv_path: str, rubric_name: str, output_path: str):
    """Generate rubric from evaluation criteria CSV"""
    click.echo(f"Generating rubric from {csv_path}...")

    generator = RubricGenerator()

    try:
        rubric = generator.generate_rubric_from_csv(Path(csv_path), rubric_name)

        generator.save_rubric_to_json(rubric, Path(output_path))

        click.echo(f"✓ Rubric generated successfully: {output_path}")
        click.echo(f"  Name: {rubric.name}")
        click.echo(f"  Criteria: {len(rubric.criteria)}")

        # Show summary
        total_points = sum(-crit.max_penalty for crit in rubric.criteria)
        click.echo(f"  Total points: {total_points:.1f}")

    except Exception as e:
        click.echo(f"✗ Error generating rubric: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option(
    "--json",
    "json_path",
    type=click.Path(exists=True),
    default="evaluation.json",
    help="Path to existing rubric JSON file",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "summary"]),
    default="summary",
    help="Output format",
)
def inspect_rubric(json_path: str, output_format: str):
    """Inspect an existing rubric"""
    click.echo(f"Loading rubric from {json_path}...")

    generator = RubricGenerator()
    rubric = generator.load_existing_rubric(Path(json_path))

    if not rubric:
        click.echo(f"✗ Could not load rubric from {json_path}", err=True)
        raise click.Abort()

    if output_format == "json":
        # Pretty print JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))

    else:  # summary format
        click.echo(f"\nRubric: {rubric.name}")
        click.echo("=" * 60)

        total_points = 0
        for i, criteria in enumerate(rubric.criteria, 1):
            points = (
                -criteria.max_penalty
            )  # Convert negative penalty to positive points
            total_points += points

            click.echo(f"\n{i}. {criteria.id}")
            click.echo(f"   Description: {criteria.description}")
            click.echo(f"   Max points: {points:.1f}")
            click.echo(f"   Rules: {len(criteria.rules)}")

            for j, rule in enumerate(criteria.rules[:3], 1):  # Show first 3 rules
                prefix = "   " if j > 1 else "   • "
                click.echo(f"{prefix}{rule.description}")
                click.echo(f"     Penalty: {rule.unit_penalty:.2f} per occurrence")

            if len(criteria.rules) > 3:
                click.echo(f"   ... and {len(criteria.rules) - 3} more rules")

        click.echo(f"\nTotal points available: {total_points:.1f}")


@main.command()
@click.option(
    "--dir",
    "directory",
    type=click.Path(exists=True),
    default="IP1_RUB",
    help="Directory containing rubric templates",
)
def list_templates(directory: str):
    """List available rubric templates"""
    dir_path = Path(directory)

    if not dir_path.exists():
        click.echo(f"Directory {directory} does not exist", err=True)
        return

    click.echo(f"Rubric templates in {directory}:")
    click.echo("-" * 40)

    json_files = list(dir_path.glob("*.json"))

    if not json_files:
        click.echo("No JSON rubric files found")
        return

    for json_file in sorted(json_files):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            rubric_name = data.get("rubric", {}).get("name", "Unnamed")
            criteria_count = len(data.get("rubric", {}).get("criteria", []))

            click.echo(f"• {json_file.name}")
            click.echo(f"  Name: {rubric_name}")
            click.echo(f"  Criteria: {criteria_count}")
            click.echo()

        except Exception as e:
            click.echo(f"• {json_file.name} (Error: {e})")
            click.echo()


@main.command()
@click.argument("exam_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--rubric",
    "rubric_path",
    type=click.Path(exists=True),
    default="evaluation.json",
    help="Path to rubric JSON file",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(),
    default="evaluations",
    help="Output directory for evaluation results",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed evaluation output")
def evaluate(exam_files, rubric_path: str, output_dir: str, verbose: bool):
    """Evaluate one or more exam files using a rubric"""
    if not exam_files:
        click.echo("No exam files specified. Use --help for usage.")
        return

    # Load rubric
    try:
        with open(rubric_path, "r", encoding="utf-8") as f:
            rubric_data = json.load(f)
    except Exception as e:
        click.echo(f"✗ Error loading rubric {rubric_path}: {e}", err=True)
        sys.exit(1)

    click.echo(f"Evaluating {len(exam_files)} exam file(s)...")
    click.echo(f"Using rubric: {rubric_path}")

    # Initialize evaluator
    analyzer = CCodeAnalyzer()
    evaluator = ExamEvaluator(analyzer)

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    results = []

    for exam_file in exam_files:
        exam_path = Path(exam_file)
        click.echo(f"\n{'=' * 60}")
        click.echo(f"Evaluating: {exam_path.name}")
        click.echo(f"{'=' * 60}")

        try:
            # Evaluate exam
            evaluation = evaluator.evaluate_exam(exam_path, rubric_data)

            # Save evaluation
            output_file = output_dir_path / f"{exam_path.stem}_evaluation.json"
            evaluator.save_evaluation(evaluation, output_file)

            results.append(
                {
                    "exam": exam_path.name,
                    "student": evaluation.student_name,
                    "points": evaluation.points_earned,
                    "total": evaluation.total_points,
                    "percentage": evaluation.grade_percentage,
                    "output_file": output_file,
                }
            )

            # Show summary
            if verbose:
                _display_detailed_evaluation(evaluation)
            else:
                _display_brief_evaluation(evaluation)

            click.echo(f"✓ Evaluation saved: {output_file}")

        except Exception as e:
            click.echo(f"✗ Error evaluating {exam_path.name}: {e}", err=True)
            results.append({"exam": exam_path.name, "error": str(e)})

    # Show final summary
    _display_final_summary(results)


def _display_brief_evaluation(evaluation):
    """Display brief evaluation summary"""
    click.echo(f"Student: {evaluation.student_name}")
    click.echo(
        f"Score: {evaluation.points_earned:.1f}/{evaluation.total_points:.1f} "
        f"({evaluation.grade_percentage:.1f}%)"
    )

    compiles = evaluation.compilation_result.get("compiles", False)
    status = "✓ Compiles" if compiles else "✗ Does not compile"
    click.echo(f"Compilation: {status}")

    if not compiles and evaluation.compilation_result.get("errors"):
        click.echo("  Errors:")
        for error in evaluation.compilation_result["errors"][:3]:  # Show first 3 errors
            click.echo(f"    • {error[:100]}...")


def _display_detailed_evaluation(evaluation):
    """Display detailed evaluation results"""
    click.echo(f"\nStudent: {evaluation.student_name}")
    click.echo(f"File: {evaluation.exam_file.name}")
    click.echo(f"{'=' * 60}")

    # Compilation info
    comp_result = evaluation.compilation_result
    click.echo("\nCompilation:")
    click.echo(f"  Status: {'SUCCESS' if comp_result.get('compiles') else 'FAILED'}")

    if comp_result.get("warnings"):
        click.echo(f"  Warnings: {len(comp_result['warnings'])}")
        if len(comp_result["warnings"]) <= 5:
            for warning in comp_result["warnings"]:
                click.echo(f"    • {warning[:80]}...")

    if comp_result.get("errors"):
        click.echo(f"  Errors: {len(comp_result['errors'])}")
        for error in comp_result["errors"][:10]:  # Show first 10 errors
            click.echo(f"    • {error[:80]}...")

    # Criteria evaluation
    click.echo(f"\nCriteria Evaluation:")
    click.echo(f"{'-' * 60}")

    for result in evaluation.evaluation_results:
        percentage = (
            (result.points_earned / result.max_points * 100)
            if result.max_points > 0
            else 0
        )
        status_char = "✓" if percentage >= 80 else "~" if percentage >= 50 else "✗"

        click.echo(f"\n{status_char} {result.criteria_id}")
        click.echo(f"  {result.criteria_description}")
        click.echo(
            f"  Points: {result.points_earned:.1f}/{result.max_points:.1f} ({percentage:.0f}%)"
        )

        if result.issues:
            click.echo(f"  Issues found: {len(result.issues)}")
            for issue in result.issues[:3]:  # Show first 3 issues
                severity_icon = (
                    "‼️"
                    if issue.severity == "error"
                    else "⚠️"
                    if issue.severity == "warning"
                    else "ℹ️"
                )
                click.echo(
                    f"    {severity_icon} Line {issue.line_number}: {issue.description}"
                )

    # Final score
    click.echo(f"\n{'=' * 60}")
    click.echo(
        f"FINAL SCORE: {evaluation.points_earned:.1f}/{evaluation.total_points:.1f}"
    )
    click.echo(f"PERCENTAGE: {evaluation.grade_percentage:.1f}%")

    # Grade letter
    grade_map = {
        (90, 100): "A",
        (80, 90): "B",
        (70, 80): "C",
        (60, 70): "D",
        (0, 60): "F",
    }

    for (low, high), letter in grade_map.items():
        if low <= evaluation.grade_percentage < high:
            click.echo(f"GRADE: {letter}")
            break


def _display_final_summary(results):
    """Display final summary of all evaluations"""
    click.echo(f"\n{'=' * 60}")
    click.echo("EVALUATION SUMMARY")
    click.echo(f"{'=' * 60}")

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    if successful:
        click.echo(f"\nSuccessfully evaluated {len(successful)} exam(s):")
        click.echo(f"{'-' * 40}")

        for result in successful:
            click.echo(f"• {result['exam']}")
            click.echo(f"  Student: {result['student']}")
            click.echo(
                f"  Score: {result['points']:.1f}/{result['total']:.1f} "
                f"({result['percentage']:.1f}%)"
            )
            click.echo(f"  Output: {result['output_file'].name}")
            click.echo()

    if failed:
        click.echo(f"\nFailed to evaluate {len(failed)} exam(s):")
        click.echo(f"{'-' * 40}")

        for result in failed:
            click.echo(f"• {result['exam']}: {result['error']}")

    if successful:
        avg_percentage = sum(r["percentage"] for r in successful) / len(successful)
        click.echo(f"\nAverage score: {avg_percentage:.1f}%")

        grades = [r["percentage"] for r in successful]
        click.echo(f"Highest: {max(grades):.1f}%")
        click.echo(f"Lowest: {min(grades):.1f}%")


if __name__ == "__main__":
    main()
