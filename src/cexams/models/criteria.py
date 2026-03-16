"""
Data models for evaluation criteria
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Subsection:
    """Represents a subsection within a criteria"""

    nombre: str
    descripcion: str
    puntos: float
    penalizacion_min: float
    anulador: bool = False


@dataclass
class Criteria:
    """Represents an evaluation criteria"""

    titulo: str
    descripcion: str
    nota_maxima: float
    subapartados: List[Subsection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Criteria":
        """Create Criteria from dictionary"""
        subapartados = []
        for sub_data in data.get("subapartados", []):
            subsection = Subsection(
                nombre=sub_data.get("nombre", ""),
                descripcion=sub_data.get("descripcion", ""),
                puntos=sub_data.get("puntos", 0.0),
                penalizacion_min=sub_data.get("penalizacion_min", 0.0),
                anulador=sub_data.get("anulador", False),
            )
            subapartados.append(subsection)

        return cls(
            titulo=data.get("titulo", ""),
            descripcion=data.get("descripcion", ""),
            nota_maxima=data.get("nota_maxima", 0.0),
            subapartados=subapartados,
        )


@dataclass
class SubsectionEvaluation:
    """Evaluation result for a subsection"""

    subsection_name: str
    subsection_description: str
    possible_points: float
    awarded_points: float
    reasoning: str


@dataclass
class CriteriaEvaluation:
    """Evaluation result for a criteria"""

    criteria_title: str
    criteria_description: str
    maximum_score: float
    awarded_score: float
    justification: str
    subsection_evaluations: List[SubsectionEvaluation] = field(default_factory=list)
    criteria_index: Optional[int] = None


@dataclass
class ExamReview:
    """Complete review results for an exam"""

    exam_name: str
    exam_file: str
    total_criteria: int
    criteria_evaluations: List[CriteriaEvaluation] = field(default_factory=list)
    overall_score: float = 0.0
    maximum_possible_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "exam_name": self.exam_name,
            "exam_file": self.exam_file,
            "total_criteria": self.total_criteria,
            "criteria_evaluations": [
                {
                    "criteria_index": eval.criteria_index,
                    "criteria_title": eval.criteria_title,
                    "criteria_description": eval.criteria_description,
                    "maximum_score": eval.maximum_score,
                    "awarded_score": eval.awarded_score,
                    "justification": eval.justification,
                    "subsection_evaluations": [
                        {
                            "subsection_name": sub.subsection_name,
                            "subsection_description": sub.subsection_description,
                            "possible_points": sub.possible_points,
                            "awarded_points": sub.awarded_points,
                            "reasoning": sub.reasoning,
                        }
                        for sub in eval.subsection_evaluations
                    ],
                }
                for eval in self.criteria_evaluations
            ],
            "overall_score": self.overall_score,
            "maximum_possible_score": self.maximum_possible_score,
        }
