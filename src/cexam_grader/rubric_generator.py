import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RubricRule:
    """Represents a single rule in a rubric criteria"""

    description: str
    unit_penalty: float
    max_occurrences: int = 1


@dataclass
class RubricCriteria:
    """Represents a criteria category in a rubric"""

    id: str
    description: str
    max_penalty: float
    rules: List[RubricRule] = field(default_factory=list)


@dataclass
class Rubric:
    """Represents a complete rubric"""

    name: str
    criteria: List[RubricCriteria] = field(default_factory=list)


class RubricGenerator:
    """Generates rubrics from evaluation criteria CSV files"""

    def __init__(self):
        self.base_rubric_templates = self._load_base_templates()

    def _load_base_templates(self) -> Dict[str, Any]:
        """Load base rubric templates from example files"""
        templates = {}
        ip1_rub_path = Path("IP1_RUB")

        if ip1_rub_path.exists():
            for json_file in ip1_rub_path.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        templates[json_file.stem] = data
                except Exception as e:
                    print(f"Warning: Could not load template {json_file}: {e}")

        return templates

    def parse_evaluation_csv(self, csv_path: Path) -> Dict[str, Any]:
        """
        Parse evaluation criteria CSV file

        Expected format:
        Row 1: Main criteria titles
        Row 2: Sub-criteria descriptions
        Row 3: Maximum points for each criteria
        """
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            if len(rows) < 3:
                raise ValueError("CSV must have at least 3 rows")

            # Clean up the data
            main_titles = [cell.strip('" ') for cell in rows[0]]
            sub_descriptions = [cell.strip('" ') for cell in rows[1]]
            max_points = [
                float(cell.strip()) if cell.strip() else 0.0 for cell in rows[2]
            ]

            # Remove empty columns
            criteria_data = []
            for title, desc, points in zip(main_titles, sub_descriptions, max_points):
                if title:  # Only include non-empty criteria
                    criteria_data.append(
                        {
                            "main_title": title,
                            "sub_description": desc,
                            "max_points": points,
                        }
                    )

            return {"criteria": criteria_data, "total_points": sum(max_points)}

        except Exception as e:
            raise ValueError(f"Error parsing CSV file {csv_path}: {e}")

    def generate_rubric_from_csv(self, csv_path: Path, rubric_name: str) -> Rubric:
        """
        Generate a rubric from evaluation criteria CSV

        Args:
            csv_path: Path to CSV file
            rubric_name: Name for the generated rubric

        Returns:
            Rubric object
        """
        csv_data = self.parse_evaluation_csv(csv_path)

        rubric = Rubric(name=rubric_name)

        for i, crit_data in enumerate(csv_data["criteria"]):
            # Generate criteria ID from title
            crit_id = self._generate_criteria_id(crit_data["main_title"], i)

            # Create criteria
            criteria = RubricCriteria(
                id=crit_id,
                description=f"{crit_data['main_title']} — {crit_data['sub_description']}",
                max_penalty=-abs(crit_data["max_points"]),  # Negative for penalties
            )

            # Add rules based on criteria type
            self._add_rules_for_criteria(criteria, crit_data)

            rubric.criteria.append(criteria)

        return rubric

    def _generate_criteria_id(self, title: str, index: int) -> str:
        """Generate a criteria ID from title"""
        # Remove special characters and convert to lowercase
        clean_id = re.sub(r"[^a-zA-Z0-9]", "_", title.lower())
        clean_id = re.sub(r"_+", "_", clean_id).strip("_")

        if not clean_id:
            clean_id = f"criteria_{index}"

        return clean_id

    def _add_rules_for_criteria(
        self, criteria: RubricCriteria, crit_data: Dict[str, Any]
    ):
        """Add appropriate rules based on criteria type"""
        title = crit_data["main_title"].lower()
        max_points = crit_data["max_points"]

        # Basic rules that apply to most criteria
        basic_rules = [
            RubricRule(
                description=f"Complete implementation of {crit_data['sub_description']}",
                unit_penalty=-max_points * 0.1,  # 10% penalty per issue
                max_occurrences=10,
            ),
            RubricRule(
                description=f"Partial implementation of {crit_data['sub_description']}",
                unit_penalty=-max_points * 0.5,  # 50% penalty
                max_occurrences=1,
            ),
            RubricRule(
                description=f"No implementation of {crit_data['sub_description']}",
                unit_penalty=-max_points,  # Full penalty
                max_occurrences=1,
            ),
        ]

        # Add type-specific rules
        if "compilación" in title or "ejecución" in title:
            criteria.rules.extend(
                [
                    RubricRule(
                        description="Compilation errors that prevent binary generation",
                        unit_penalty=-max_points,
                        max_occurrences=1,
                    ),
                    RubricRule(
                        description="Runtime errors or segmentation faults",
                        unit_penalty=-max_points * 0.5,
                        max_occurrences=2,
                    ),
                ]
            )
        elif "indentación" in title or "estructura" in title:
            criteria.rules.extend(
                [
                    RubricRule(
                        description="Inconsistent indentation or formatting",
                        unit_penalty=-max_points * 0.1,
                        max_occurrences=5,
                    ),
                    RubricRule(
                        description="Chaotic indentation making code unreadable",
                        unit_penalty=-max_points,
                        max_occurrences=1,
                    ),
                ]
            )
        elif "variables" in title or "declaración" in title:
            criteria.rules.extend(
                [
                    RubricRule(
                        description="Incorrect variable declarations",
                        unit_penalty=-max_points * 0.1,
                        max_occurrences=5,
                    ),
                    RubricRule(
                        description="Uninitialized variables",
                        unit_penalty=-max_points * 0.2,
                        max_occurrences=3,
                    ),
                ]
            )

        # Add basic rules
        criteria.rules.extend(basic_rules)

    def save_rubric_to_json(self, rubric: Rubric, output_path: Path):
        """Save rubric to JSON file"""
        rubric_dict = {"rubric": {"name": rubric.name, "criteria": []}}

        for criteria in rubric.criteria:
            crit_dict = {
                "id": criteria.id,
                "description": criteria.description,
                "max_penalty": criteria.max_penalty,
                "rules": [],
            }

            for rule in criteria.rules:
                rule_dict = {
                    "description": rule.description,
                    "unit_penalty": rule.unit_penalty,
                }
                if rule.max_occurrences > 1:
                    rule_dict["max_occurrences"] = rule.max_occurrences

                crit_dict["rules"].append(rule_dict)

            rubric_dict["rubric"]["criteria"].append(crit_dict)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rubric_dict, f, indent=2, ensure_ascii=False)

    def load_existing_rubric(self, json_path: Path) -> Optional[Rubric]:
        """Load an existing rubric from JSON file"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            rubric_data = data.get("rubric", {})
            rubric = Rubric(name=rubric_data.get("name", "Unnamed Rubric"))

            for crit_data in rubric_data.get("criteria", []):
                criteria = RubricCriteria(
                    id=crit_data.get("id", ""),
                    description=crit_data.get("description", ""),
                    max_penalty=crit_data.get("max_penalty", 0),
                )

                for rule_data in crit_data.get("rules", []):
                    rule = RubricRule(
                        description=rule_data.get("description", ""),
                        unit_penalty=rule_data.get("unit_penalty", 0),
                        max_occurrences=rule_data.get("max_occurrences", 1),
                    )
                    criteria.rules.append(rule)

                rubric.criteria.append(criteria)

            return rubric

        except Exception as e:
            print(f"Error loading rubric from {json_path}: {e}")
            return None
