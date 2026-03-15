import click
import json
from pathlib import Path
from typing import Optional

from .rubric_generator import RubricGenerator


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
def evaluate(exam_files, rubric_path: str, output_dir: str):
    """Evaluate one or more exam files using a rubric"""
    if not exam_files:
        click.echo("No exam files specified. Use --help for usage.")
        return

    click.echo(f"Evaluating {len(exam_files)} exam file(s)...")
    click.echo(f"Using rubric: {rubric_path}")

    # TODO: Implement actual evaluation logic
    click.echo("\nEvaluation results will be saved to:")
    for exam_file in exam_files:
        exam_name = Path(exam_file).stem
        output_file = Path(output_dir) / f"{exam_name}_evaluation.json"
        click.echo(f"  • {exam_file} → {output_file}")

    click.echo("\nNote: Evaluation logic not yet implemented.")


if __name__ == "__main__":
    main()
