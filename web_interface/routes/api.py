from flask import Blueprint, request, jsonify
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from config import EXAMS_DIR, CRITERIA_DIR, REVIEWS_DIR
from services import ExamEvaluator

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/files/exams")
def get_exams():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    return jsonify({"exams": exam_files})


@api_bp.route("/files/criteria")
def get_criteria_files():
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])
    return jsonify({"criteria_files": criteria_files})


@api_bp.route("/criteria/<criteria_file>")
def get_criteria(criteria_file):
    filepath = os.path.join(CRITERIA_DIR, criteria_file)
    if not os.path.exists(filepath):
        return jsonify({"error": "Criteria file not found"}), 404

    with open(filepath, "r", encoding="utf-8") as f:
        criteria_list = json.load(f)

    if not isinstance(criteria_list, list):
        return jsonify({"error": "Criteria must be a list"})

    criteria_with_index = []
    for i, crit in enumerate(criteria_list):
        criteria_with_index.append(
            {
                "index": i,
                "titulo": crit.get("titulo", f"Criteria {i + 1}"),
                "descripcion": crit.get("descripcion", ""),
                "nota_maxima": crit.get("nota_maxima", 0),
                "subapartados": crit.get("subapartados", []),
            }
        )

    return jsonify(
        {
            "criteria_file": criteria_file,
            "total_criteria": len(criteria_list),
            "criteria": criteria_with_index,
        }
    )


@api_bp.route("/criteria/save", methods=["POST"])
def save_criteria():
    data = request.json
    criteria_file = data.get("criteria_file")
    criteria_list = data.get("criteria")

    if not criteria_file or criteria_list is None:
        return jsonify({"success": False, "error": "Missing data"})

    filepath = os.path.join(CRITERIA_DIR, criteria_file)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(criteria_list, f, indent=2, ensure_ascii=False)
        return jsonify({"success": True, "message": "Saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


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


@api_bp.route("/run/single-criteria", methods=["POST"])
def run_single_criteria_review():
    data = request.json
    exam_file = data.get("exam_file")
    criteria_file = data.get("criteria_file")
    criteria_index = data.get("criteria_index", 0)

    if not exam_file or not criteria_file:
        return jsonify({"success": False, "error": "Missing exam or criteria"})

    try:
        evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
        result = evaluator.run_single_criteria_review(exam_file, criteria_file, criteria_index)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@api_bp.route("/run/parallel", methods=["POST"])
def run_parallel_review():
    data = request.json
    criteria_file = data.get("criteria_file")
    max_workers = int(data.get("max_workers", 2))

    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])

    if not exam_files:
        return jsonify({"success": False, "error": "No exam files found"})

    if not criteria_file:
        return jsonify({"success": False, "error": "Missing criteria file"})

    results = []
    errors = []

    def process_exam(exam_file):
        try:
            evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
            result = evaluator.run_single_review(exam_file, criteria_file)
            return {"exam": exam_file, "success": True, "result": result}
        except Exception as e:
            return {"exam": exam_file, "success": False, "error": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_exam, exam): exam for exam in exam_files}

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results.append(result)
            else:
                errors.append(result)

    return jsonify(
        {
            "success": True,
            "processed": len(results) + len(errors),
            "success_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
        }
    )


@api_bp.route("/run/parallel-criteria", methods=["POST"])
def run_parallel_criteria_review():
    data = request.json
    criteria_file = data.get("criteria_file")
    max_workers = int(data.get("max_workers", 2))
    target_criteria_index = data.get("criteria_index")

    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])

    if not exam_files:
        return jsonify({"success": False, "error": "No exam files found"})

    if not criteria_file:
        return jsonify({"success": False, "error": "Missing criteria file"})

    results = []
    errors = []

    def process_exam(exam_file):
        try:
            evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
            result = evaluator.run_single_criteria_review(
                exam_file, criteria_file, target_criteria_index
            )
            return {"exam": exam_file, "success": True, "result": result}
        except Exception as e:
            return {"exam": exam_file, "success": False, "error": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_exam, exam): exam for exam in exam_files}

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results.append(result)
            else:
                errors.append(result)

    return jsonify(
        {
            "success": True,
            "processed": len(results) + len(errors),
            "success_count": len(results),
            "error_count": len(errors),
            "results": results,
            "errors": errors,
        }
    )


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


@api_bp.route("/reviewer/data")
def reviewer_data():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    exam_idx = int(request.args.get("exam_idx", 0))
    criteria_file = request.args.get("criteria_file", criteria_files[0] if criteria_files else None)
    criteria_idx = int(request.args.get("criteria_idx", 0))

    if not criteria_file or exam_idx >= len(exam_files):
        return jsonify({"error": "No data available"})

    exam_file = exam_files[exam_idx]

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

    criteria_with_index = []
    for i, crit in enumerate(criteria_data):
        criteria_with_index.append(
            {
                "index": i,
                "titulo": crit.get("titulo", f"Criteria {i + 1}"),
                "descripcion": crit.get("descripcion", ""),
                "nota_maxima": crit.get("nota_maxima", 0),
                "subapartados": crit.get("subapartados", []),
            }
        )

    return jsonify(
        {
            "exam_file": exam_file,
            "criteria_file": criteria_file,
            "exam_content": exam_content,
            "criteria_data": criteria_data,
            "criteria_with_index": criteria_with_index,
            "review_data": review_data,
            "exam_idx": exam_idx,
            "criteria_idx": criteria_idx,
            "total_exams": len(exam_files),
            "total_criteria": len(criteria_data),
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
