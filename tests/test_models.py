"""Tests for CExams models"""

import pytest
from cexams.models.criteria import (
    Subsection,
    Criteria,
    SubsectionEvaluation,
    CriteriaEvaluation,
    ExamReview,
)


class TestSubsection:
    """Tests for Subsection model"""

    def test_subsection_creation(self):
        subsection = Subsection(
            nombre="Test Subsection",
            descripcion="Test description",
            puntos=2.5,
            penalizacion_min=0.0,
            anulador=False,
        )
        assert subsection.nombre == "Test Subsection"
        assert subsection.puntos == 2.5


class TestCriteria:
    """Tests for Criteria model"""

    def test_criteria_creation(self):
        criteria = Criteria(
            titulo="Test Criteria",
            descripcion="Test description",
            nota_maxima=10.0,
            subapartados=[],
        )
        assert criteria.titulo == "Test Criteria"
        assert criteria.nota_maxima == 10.0

    def test_criteria_from_dict(self):
        data = {
            "titulo": "Test Criteria",
            "descripcion": "Test description",
            "nota_maxima": 10.0,
            "subapartados": [
                {
                    "nombre": "Sub 1",
                    "descripcion": "Sub description",
                    "puntos": 5.0,
                    "penalizacion_min": 0.0,
                    "anulador": False,
                }
            ],
        }
        criteria = Criteria.from_dict(data)
        assert criteria.titulo == "Test Criteria"
        assert len(criteria.subapartados) == 1
        assert criteria.subapartados[0].puntos == 5.0


class TestExamReview:
    """Tests for ExamReview model"""

    def test_exam_review_creation(self):
        review = ExamReview(
            exam_name="test_exam",
            exam_file="test_exam.c",
            total_criteria=3,
        )
        assert review.exam_name == "test_exam"
        assert review.overall_score == 0.0
        assert review.maximum_possible_score == 0.0

    def test_exam_review_to_dict(self):
        review = ExamReview(
            exam_name="test_exam",
            exam_file="test_exam.c",
            total_criteria=1,
            overall_score=7.5,
            maximum_possible_score=10.0,
        )
        review_dict = review.to_dict()
        assert review_dict["exam_name"] == "test_exam"
        assert review_dict["overall_score"] == 7.5
        assert review_dict["maximum_possible_score"] == 10.0
