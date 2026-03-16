from flask import Blueprint, request, jsonify
import os
import json

from config import EXAMS_DIR, CRITERIA_DIR, REVIEWS_DIR
from services import ExamEvaluator

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/run/single", methods=["POST"])
def run_single_review():
    data = request.json
    exam_file = data.get("exam_file")
    criteria_file = data.get("criteria_file")

    if not exam_file or not criteria_file:
        return jsonify({"success": False, "error": "Missing exam or criteria"})

    try:
        evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
        result = evaluator.run_single_review(exam_file, criteria_file)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@api_bp.route("/run/batch", methods=["POST"])
def run_batch_review():
    data = request.json
    criteria_file = data.get("criteria_file")

    if not criteria_file:
        return jsonify({"success": False, "error": "Missing criteria file"})

    try:
        evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
        count = evaluator.run_all_reviews(criteria_file)
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@api_bp.route("/run/status/<exam_idx>/<criteria_idx>")
def get_review_status(exam_idx, criteria_idx):
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    exam_idx = int(exam_idx)
    criteria_idx = int(criteria_idx)

    current_exam = exam_files[exam_idx] if exam_idx < len(exam_files) else None
    total_exams = len(exam_files)
    total_criteria = len(criteria_files)

    return jsonify(
        {
            "current_exam": current_exam,
            "exam_idx": exam_idx,
            "criteria_idx": criteria_idx,
            "total_exams": total_exams,
            "total_criteria": total_criteria,
            "progress": f"Exam {exam_idx + 1}/{total_exams}, Criteria {criteria_idx + 1}/{total_criteria}",
        }
    )


@api_bp.route("/reviewer/data")
def reviewer_data():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    exam_idx = int(request.args.get("exam_idx", 0))
    criteria_idx = int(request.args.get("criteria_idx", 0))

    if exam_idx >= len(exam_files) or criteria_idx >= len(criteria_files):
        return jsonify({"error": "Index out of range"})

    exam_file = exam_files[exam_idx]
    criteria_file = criteria_files[criteria_idx]

    exam_path = os.path.join(EXAMS_DIR, exam_file)
    with open(exam_path, "r", encoding="utf-8") as f:
        exam_content = f.read()

    criteria_path = os.path.join(CRITERIA_DIR, criteria_file)
    with open(criteria_path, "r", encoding="utf-8") as f:
        criteria_data = json.load(f)

    review_file = os.path.join(REVIEWS_DIR, f"{os.path.splitext(exam_file)[0]}_review.json")
    review_data = None
    if os.path.exists(review_file):
        with open(review_file, "r", encoding="utf-8") as f:
            review_data = json.load(f)

    current_evaluation = None
    if review_data and review_data.get("criteria_evaluations"):
        for eval_item in review_data.get("criteria_evaluations", []):
            if eval_item.get("criteria_index") == criteria_idx + 1:
                current_evaluation = eval_item
                break

    return jsonify(
        {
            "exam_file": exam_file,
            "criteria_file": criteria_file,
            "exam_content": exam_content,
            "criteria_data": criteria_data,
            "review_data": review_data,
            "exam_idx": exam_idx,
            "criteria_idx": criteria_idx,
            "total_exams": len(exam_files),
            "total_criteria": len(criteria_files),
            "current_criteria": criteria_data[criteria_idx]
            if criteria_idx < len(criteria_data)
            else None,
            "current_evaluation": current_evaluation,
        }
    )


@api_bp.route("/reviewer/save-evaluation", methods=["POST"])
def save_evaluation():
    data = request.json

    exam_file = data.get("exam_file")
    criteria_idx = data.get("criteria_idx")
    evaluation = data.get("evaluation")

    review_file = os.path.join(REVIEWS_DIR, f"{os.path.splitext(exam_file)[0]}_review.json")

    if os.path.exists(review_file):
        with open(review_file, "r", encoding="utf-8") as f:
            review_data = json.load(f)
    else:
        review_data = {
            "exam_name": os.path.splitext(exam_file)[0],
            "exam_file": exam_file,
            "total_criteria": 0,
            "criteria_evaluations": [],
            "overall_score": 0.0,
            "maximum_possible_score": 0.0,
        }

    found = False
    for i, eval_item in enumerate(review_data["criteria_evaluations"]):
        if eval_item.get("criteria_index") == criteria_idx + 1:
            review_data["criteria_evaluations"][i] = evaluation
            found = True
            break

    if not found:
        review_data["criteria_evaluations"].append(evaluation)

    overall_score = sum(e.get("awarded_score", 0) for e in review_data["criteria_evaluations"])
    review_data["overall_score"] = overall_score

    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    return jsonify({"success": True, "message": "Evaluation saved"})
