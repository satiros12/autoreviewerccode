import subprocess
import tempfile
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import shlex


@dataclass
class CodeIssue:
    """Represents an issue found in code analysis"""

    rule_id: str
    description: str
    line_number: int
    severity: str  # 'error', 'warning', 'info'
    penalty_applied: float
    context: str = ""


@dataclass
class EvaluationResult:
    """Represents the evaluation result for a single criteria"""

    criteria_id: str
    criteria_description: str
    max_points: float
    points_earned: float
    issues: List[CodeIssue] = field(default_factory=list)
    notes: str = ""


@dataclass
class ExamEvaluation:
    """Represents complete evaluation of an exam"""

    exam_file: Path
    student_name: str = ""
    total_points: float = 0.0
    points_earned: float = 0.0
    grade_percentage: float = 0.0
    evaluation_results: List[EvaluationResult] = field(default_factory=list)
    compilation_result: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)


class CCodeAnalyzer:
    """Analyzes C code for various issues and patterns"""

    def __init__(self):
        self.compiler_flags = ["-Wall", "-Wextra", "-Werror", "-pedantic"]

    def extract_student_info(self, file_path: Path) -> Dict[str, str]:
        """Extract student information from filename and file content"""
        info = {
            "filename": file_path.name,
            "student_name": self._extract_name_from_filename(file_path.name),
            "file_size": file_path.stat().st_size,
        }

        # Try to extract from file content
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1000)  # Read first 1000 chars

                # Look for comments with student info
                name_patterns = [
                    r"Nombre:\s*([^\n]+)",
                    r"Student:\s*([^\n]+)",
                    r"Author:\s*([^\n]+)",
                    r"Alumno:\s*([^\n]+)",
                ]

                for pattern in name_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        info["student_name"] = match.group(1).strip()
                        break

        except Exception:
            pass

        return info

    def _extract_name_from_filename(self, filename: str) -> str:
        """Extract student name from filename patterns"""
        # Common patterns in exam filenames
        patterns = [
            r"([A-Z][a-z]+)_",  # First name followed by underscore
            r"Assignment.*_([a-z]+\.[a-z]+)_",  # first.last format
            r"([A-Za-z]+)_exam",  # Name before 'exam'
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                name = match.group(1)
                # Clean up the name
                name = name.replace("_", " ").replace(".", " ").title()
                return name

        return "Unknown Student"

    def check_compilation(self, file_path: Path) -> Dict[str, Any]:
        """Check if C code compiles successfully"""
        result = {
            "compiles": False,
            "errors": [],
            "warnings": [],
            "output": "",
            "executable_path": None,
        }

        with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as tmp_exe:
            executable_path = tmp_exe.name

        try:
            # Try to compile
            compile_cmd = (
                ["gcc"] + self.compiler_flags + [str(file_path), "-o", executable_path]
            )

            process = subprocess.run(
                compile_cmd, capture_output=True, text=True, timeout=30
            )

            result["output"] = process.stdout + process.stderr
            result["compiles"] = process.returncode == 0

            # Parse errors and warnings
            if process.stderr:
                for line in process.stderr.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if "error:" in line:
                        result["errors"].append(line)
                    elif "warning:" in line:
                        result["warnings"].append(line)

            if result["compiles"]:
                result["executable_path"] = executable_path
            else:
                Path(executable_path).unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            result["errors"].append("Compilation timed out (30 seconds)")
            Path(executable_path).unlink(missing_ok=True)
        except Exception as e:
            result["errors"].append(f"Compilation failed: {str(e)}")
            Path(executable_path).unlink(missing_ok=True)

        return result

    def analyze_code_structure(self, file_path: Path) -> List[CodeIssue]:
        """Analyze code structure and style"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Check for basic structure issues
            issue_finders = [
                self._check_indentation,
                self._check_comments,
                self._check_function_declarations,
                self._check_variable_declarations,
                self._check_control_structures,
            ]

            for finder in issue_finders:
                issues.extend(finder(lines))

        except Exception as e:
            issues.append(
                CodeIssue(
                    rule_id="analysis_error",
                    description=f"Could not analyze code structure: {str(e)}",
                    line_number=0,
                    severity="error",
                    penalty_applied=0.0,
                )
            )

        return issues

    def _check_indentation(self, lines: List[str]) -> List[CodeIssue]:
        """Check for indentation issues"""
        issues = []
        in_block_comment = False

        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("//"):
                continue

            # Handle block comments
            if "/*" in line and "*/" not in line:
                in_block_comment = True
                continue
            if in_block_comment:
                if "*/" in line:
                    in_block_comment = False
                continue

            # Check for mixed tabs and spaces
            if "\t" in line and " " in line[:8]:  # Check first 8 chars
                leading = line[: len(line) - len(stripped)]
                if " " in leading and "\t" in leading:
                    issues.append(
                        CodeIssue(
                            rule_id="indentation_mixed",
                            description="Mixed tabs and spaces in indentation",
                            line_number=i,
                            severity="warning",
                            penalty_applied=-0.1,
                            context=line[:40] + "..." if len(line) > 40 else line,
                        )
                    )

            # Check for inconsistent indentation (basic check)
            if stripped and line[0] != " " and line[0] != "\t":
                # Code not indented at all (could be global scope)
                pass

        return issues

    def _check_comments(self, lines: List[str]) -> List[CodeIssue]:
        """Check for comments"""
        issues = []
        total_lines = len(lines)
        comment_lines = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or "/*" in line or "*/" in line:
                comment_lines += 1

        # Check if there are very few or no comments
        if total_lines > 20 and comment_lines == 0:
            issues.append(
                CodeIssue(
                    rule_id="no_comments",
                    description="No comments found in code",
                    line_number=0,
                    severity="warning",
                    penalty_applied=-0.25,
                )
            )

        return issues

    def _check_function_declarations(self, lines: List[str]) -> List[CodeIssue]:
        """Check function declarations and definitions"""
        issues = []
        function_pattern = r"^\s*(\w+\s+)+(\w+)\s*\([^)]*\)\s*{?\s*$"

        for i, line in enumerate(lines, 1):
            if re.match(function_pattern, line):
                # Check for missing return type
                if not re.search(
                    r"^\s*(void|int|float|double|char|struct\s+\w+|unsigned)", line
                ):
                    issues.append(
                        CodeIssue(
                            rule_id="function_missing_type",
                            description="Function may be missing return type",
                            line_number=i,
                            severity="warning",
                            penalty_applied=-0.1,
                            context=line.strip(),
                        )
                    )

        return issues

    def _check_variable_declarations(self, lines: List[str]) -> List[CodeIssue]:
        """Check variable declarations"""
        issues = []
        var_pattern = r"^\s*(int|float|double|char|struct\s+\w+)\s+\w+"

        for i, line in enumerate(lines, 1):
            if re.match(var_pattern, line):
                # Check for uninitialized variables that should be initialized
                if "=" not in line and ";" in line:
                    # This is a simple check - in practice might need more context
                    pass

        return issues

    def _check_control_structures(self, lines: List[str]) -> List[CodeIssue]:
        """Check control structures"""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check for assignment in condition (common mistake)
            if re.search(r"if\s*\([^=]*=[^=].*\)", line):
                issues.append(
                    CodeIssue(
                        rule_id="assignment_in_condition",
                        description="Possible assignment (=) instead of comparison (==) in condition",
                        line_number=i,
                        severity="error",
                        penalty_applied=-0.25,
                        context=line.strip(),
                    )
                )

            # Check for goto (generally discouraged)
            if "goto " in line:
                issues.append(
                    CodeIssue(
                        rule_id="goto_used",
                        description="Use of goto statement",
                        line_number=i,
                        severity="warning",
                        penalty_applied=-0.5,
                        context=line.strip(),
                    )
                )

        return issues

    def check_specific_patterns(
        self, file_path: Path, patterns: List[Dict[str, Any]]
    ) -> List[CodeIssue]:
        """Check for specific patterns in the code"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern_info in patterns:
                pattern = pattern_info.get("pattern", "")
                rule_id = pattern_info.get("rule_id", "pattern_check")
                description = pattern_info.get("description", "Pattern check")
                severity = pattern_info.get("severity", "info")
                penalty = pattern_info.get("penalty", 0.0)

                matches = list(
                    re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                )

                if matches:
                    for match in matches:
                        # Find line number
                        line_num = content[: match.start()].count("\n") + 1

                        issues.append(
                            CodeIssue(
                                rule_id=rule_id,
                                description=description,
                                line_number=line_num,
                                severity=severity,
                                penalty_applied=penalty,
                                context=match.group(0)[:100] + "..."
                                if len(match.group(0)) > 100
                                else match.group(0),
                            )
                        )

        except Exception as e:
            issues.append(
                CodeIssue(
                    rule_id="pattern_check_error",
                    description=f"Error checking patterns: {str(e)}",
                    line_number=0,
                    severity="error",
                    penalty_applied=0.0,
                )
            )

        return issues


class ExamEvaluator:
    """Evaluates exams using rubrics"""

    def __init__(self, analyzer: CCodeAnalyzer = None):
        self.analyzer = analyzer or CCodeAnalyzer()

    def evaluate_exam(
        self, exam_file: Path, rubric_data: Dict[str, Any]
    ) -> ExamEvaluation:
        """Evaluate an exam file using a rubric"""

        # Extract student info
        student_info = self.analyzer.extract_student_info(exam_file)

        # Create evaluation object
        evaluation = ExamEvaluation(
            exam_file=exam_file,
            student_name=student_info.get("student_name", "Unknown Student"),
        )

        # Check compilation
        compilation_result = self.analyzer.check_compilation(exam_file)
        evaluation.compilation_result = compilation_result

        # Analyze code structure
        structure_issues = self.analyzer.analyze_code_structure(exam_file)

        # Get rubric criteria - handle both formats
        if isinstance(rubric_data, list):
            # Format like evaluation.json - list of criteria
            rubric_criteria = self._convert_list_format_to_criteria(rubric_data)
        else:
            # Format like IP1_RUB files - dict with 'rubric' key
            rubric_criteria = rubric_data.get("rubric", {}).get("criteria", [])

        # Evaluate each criteria
        total_points = 0
        points_earned = 0

        for crit_data in rubric_criteria:
            crit_id = crit_data.get("id", "")
            crit_description = crit_data.get("description", "")
            max_penalty = crit_data.get("max_penalty", 0)
            max_points = -max_penalty  # Convert negative penalty to positive points

            result = EvaluationResult(
                criteria_id=crit_id,
                criteria_description=crit_description,
                max_points=max_points,
                points_earned=max_points,  # Start with full points, deduct for issues
            )

            # Apply rules for this criteria
            rules = crit_data.get("rules", [])
            for rule in rules:
                rule_penalty = rule.get("unit_penalty", 0)

                # Check if this rule applies to code structure issues
                # This is a simplified implementation
                # In a full implementation, you would map rules to specific checks

                # For now, apply penalties based on general issues
                if (
                    "indentation" in crit_id.lower()
                    or "estructura" in crit_description.lower()
                ):
                    # Apply indentation-related penalties
                    indentation_issues = [
                        issue
                        for issue in structure_issues
                        if "indentation" in issue.rule_id
                    ]
                    if indentation_issues:
                        result.points_earned += rule_penalty * min(
                            len(indentation_issues), 5
                        )
                        result.issues.extend(indentation_issues[:5])  # Limit to 5

            # Ensure points don't go below 0
            result.points_earned = max(0, result.points_earned)

            total_points += max_points
            points_earned += result.points_earned

            evaluation.evaluation_results.append(result)

        # Apply compilation penalties
        if not compilation_result["compiles"]:
            # Find compilation criteria
            for result in evaluation.evaluation_results:
                if "compilación" in result.criteria_description.lower():
                    result.points_earned = 0
                    result.issues.append(
                        CodeIssue(
                            rule_id="compilation_failed",
                            description="Code does not compile",
                            line_number=0,
                            severity="error",
                            penalty_applied=-result.max_points,
                        )
                    )
                    # Recalculate points
                    points_earned -= result.max_points

        evaluation.total_points = total_points
        evaluation.points_earned = points_earned
        evaluation.grade_percentage = (
            (points_earned / total_points * 100) if total_points > 0 else 0
        )

        return evaluation

    def save_evaluation(self, evaluation: ExamEvaluation, output_path: Path):
        """Save evaluation results to JSON file"""
        output_dict = {
            "exam_file": str(evaluation.exam_file),
            "student_name": evaluation.student_name,
            "total_points": evaluation.total_points,
            "points_earned": evaluation.points_earned,
            "grade_percentage": evaluation.grade_percentage,
            "evaluation_results": [],
            "compilation": evaluation.compilation_result,
            "summary": self._generate_summary(evaluation),
        }

        for result in evaluation.evaluation_results:
            result_dict = {
                "criteria_id": result.criteria_id,
                "criteria_description": result.criteria_description,
                "max_points": result.max_points,
                "points_earned": result.points_earned,
                "notes": result.notes,
                "issues": [],
            }

            for issue in result.issues:
                issue_dict = {
                    "rule_id": issue.rule_id,
                    "description": issue.description,
                    "line_number": issue.line_number,
                    "severity": issue.severity,
                    "penalty_applied": issue.penalty_applied,
                    "context": issue.context,
                }
                result_dict["issues"].append(issue_dict)

            output_dict["evaluation_results"].append(result_dict)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_dict, f, indent=2, ensure_ascii=False)

    def _generate_summary(self, evaluation: ExamEvaluation) -> Dict[str, Any]:
        """Generate a summary of the evaluation"""
        total_issues = sum(
            len(result.issues) for result in evaluation.evaluation_results
        )
        critical_issues = sum(
            1
            for result in evaluation.evaluation_results
            for issue in result.issues
            if issue.severity == "error"
        )

        grade_letter = self._calculate_grade_letter(evaluation.grade_percentage)

        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "grade_letter": grade_letter,
            "compilation_status": "SUCCESS"
            if evaluation.compilation_result.get("compiles")
            else "FAILED",
            "warnings_count": len(evaluation.compilation_result.get("warnings", [])),
        }

    def _calculate_grade_letter(self, percentage: float) -> str:
        """Calculate letter grade from percentage"""
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    def _convert_list_format_to_criteria(
        self, criteria_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert evaluation.json format to IP1_RUB format"""
        converted_criteria = []

        for i, crit in enumerate(criteria_list):
            # Generate ID from title
            title = crit.get("titulo", "")
            clean_id = re.sub(r"[^a-zA-Z0-9]", "_", title.lower())
            clean_id = re.sub(r"_+", "_", clean_id).strip("_")
            if not clean_id:
                clean_id = f"criteria_{i}"

            # Convert subapartados to rules
            rules = []
            subapartados = crit.get("subapartados", [])

            for sub in subapartados:
                rule = {
                    "description": sub.get("descripcion", ""),
                    "unit_penalty": -sub.get("puntos", 0.0),  # Negative for penalties
                }

                if sub.get("anulador"):
                    rule["severity"] = "error"

                rules.append(rule)

            # Add the criteria
            converted_criteria.append(
                {
                    "id": clean_id,
                    "description": crit.get("descripcion", ""),
                    "max_penalty": -crit.get(
                        "nota_maxima", 0.0
                    ),  # Negative for penalties
                    "rules": rules,
                }
            )

        return converted_criteria
