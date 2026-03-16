import os
import json
import shutil
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
    flash,
)
from werkzeug.utils import secure_filename
from api.evaluator import ExamEvaluator

app = Flask(__name__)
app.secret_key = "cexams-secret-key-change-in-production"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMS_DIR = os.path.join(BASE_DIR, "exams")
CRITERIA_DIR = os.path.join(BASE_DIR, "criteria")
REVIEWS_DIR = os.path.join(BASE_DIR, "reviews")

for directory in [EXAMS_DIR, CRITERIA_DIR, REVIEWS_DIR]:
    os.makedirs(directory, exist_ok=True)

ALLOWED_EXTENSIONS = {"c", "json"}


def allowed_file(filename, allowed_extensions=ALLOWED_EXTENSIONS):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@app.route("/")
def index():
    exam_files = [f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")]
    criteria_files = [f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")]
    review_files = [f for f in os.listdir(REVIEWS_DIR) if f.endswith(".json")]

    return render_template(
        "index.html",
        exam_count=len(exam_files),
        criteria_count=len(criteria_files),
        review_count=len(review_files),
        exam_files=sorted(exam_files),
        criteria_files=sorted(criteria_files),
    )


@app.route("/upload/exams", methods=["POST"])
def upload_exams():
    if "files[]" not in request.files:
        flash("No files selected", "error")
        return redirect(url_for("index"))

    files = request.files.getlist("files[]")
    uploaded = 0
    for file in files:
        if file and allowed_file(file.filename, {"c"}):
            filename = secure_filename(file.filename)
            file.save(os.path.join(EXAMS_DIR, filename))
            uploaded += 1

    flash(f"Uploaded {uploaded} exam files", "success")
    return redirect(url_for("index"))


@app.route("/upload/criteria", methods=["POST"])
def upload_criteria():
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file and allowed_file(file.filename, {"json"}):
        filename = secure_filename(file.filename)
        file.save(os.path.join(CRITERIA_DIR, filename))
        flash(f"Uploaded criteria: {filename}", "success")

    return redirect(url_for("index"))


@app.route("/exams")
def list_exams():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    return render_template("exams.html", exam_files=exam_files)


@app.route("/exam/<path:filename>")
def view_exam(filename):
    filepath = os.path.join(EXAMS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return render_template("exam_view.html", filename=filename, content=content)
    return "File not found", 404


@app.route("/criteria")
def list_criteria():
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])
    return render_template("criteria_list.html", criteria_files=criteria_files)


@app.route("/criteria/<filename>")
def view_criteria(filename):
    filepath = os.path.join(CRITERIA_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            criteria_json = json.loads(content)
        except json.JSONDecodeError:
            criteria_json = None
        return render_template(
            "criteria_editor.html", filename=filename, content=content, criteria=criteria_json
        )
    return "File not found", 404


@app.route("/criteria/<filename>/save", methods=["POST"])
def save_criteria(filename):
    filepath = os.path.join(CRITERIA_DIR, secure_filename(filename))
    new_content = request.form.get("content")

    try:
        json.loads(new_content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        flash("Criteria saved successfully", "success")
    except json.JSONDecodeError as e:
        flash(f"Invalid JSON: {str(e)}", "error")

    return redirect(url_for("view_criteria", filename=filename))


@app.route("/reviews")
def list_reviews():
    review_files = sorted([f for f in os.listdir(REVIEWS_DIR) if f.endswith(".json")])
    reviews = []
    for rf in review_files:
        filepath = os.path.join(REVIEWS_DIR, rf)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        reviews.append(
            {
                "filename": rf,
                "exam_name": data.get("exam_name", rf),
                "overall_score": data.get("overall_score", 0),
                "maximum_score": data.get("maximum_possible_score", 0),
            }
        )
    return render_template("reviews.html", reviews=reviews)


@app.route("/review/<filename>")
def view_review(filename):
    filepath = os.path.join(REVIEWS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            review = json.load(f)

        exam_file = os.path.join(EXAMS_DIR, review.get("exam_file", ""))
        exam_content = ""
        if os.path.exists(exam_file):
            with open(exam_file, "r", encoding="utf-8") as f:
                exam_content = f.read()

        return render_template("review_detail.html", review=review, exam_content=exam_content)
    return "Review not found", 404


@app.route("/review/<filename>/download")
def download_review(filename):
    return send_from_directory(REVIEWS_DIR, secure_filename(filename), as_attachment=True)


@app.route("/run", methods=["GET", "POST"])
def run_review():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    selected_exam = (
        request.args.get("exam") if request.method == "GET" else request.form.get("exam")
    )
    selected_criteria = (
        request.args.get("criteria") if request.method == "GET" else request.form.get("criteria")
    )

    result = None
    error = None

    if request.method == "POST" and "run_single" in request.form:
        if not selected_exam or not selected_criteria:
            error = "Please select both exam and criteria"
        else:
            try:
                evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
                result = evaluator.run_single_review(selected_exam, selected_criteria)
                flash(f"Review completed for {selected_exam}", "success")
            except Exception as e:
                error = str(e)

    elif request.method == "POST" and "run_all" in request.form:
        if not criteria_files:
            error = "No criteria files available"
        else:
            try:
                evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
                count = evaluator.run_all_reviews(criteria_files[0])
                flash(f"Completed {count} reviews", "success")
            except Exception as e:
                error = str(e)

    return render_template(
        "run_review.html",
        exam_files=exam_files,
        criteria_files=criteria_files,
        selected_exam=selected_exam,
        selected_criteria=selected_criteria,
        result=result,
        error=error,
    )


@app.route("/reviewer")
def reviewer():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    if not exam_files or not criteria_files:
        return render_template(
            "reviewer.html",
            exam_files=exam_files,
            criteria_files=criteria_files,
            exam_content="",
            criteria_data=None,
            review_data=None,
            current_exam_idx=0,
            current_criteria_idx=0,
            error="No exams or criteria available",
        )

    return render_template(
        "reviewer.html",
        exam_files=exam_files,
        criteria_files=criteria_files,
        exam_content="",
        criteria_data=None,
        review_data=None,
        current_exam_idx=0,
        current_criteria_idx=0,
    )


@app.route("/reviewer/data")
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
            "current_review": None,
        }
    )


@app.route("/reviewer/save-evaluation", methods=["POST"])
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

    if criteria_idx < len(review_data["criteria_evaluations"]):
        review_data["criteria_evaluations"][criteria_idx] = evaluation
    else:
        review_data["criteria_evaluations"].append(evaluation)

    overall_score = sum(e.get("awarded_score", 0) for e in review_data["criteria_evaluations"])
    review_data["overall_score"] = overall_score

    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(review_data, f, indent=2, ensure_ascii=False)

    return jsonify({"success": True, "message": "Evaluation saved"})


@app.route("/delete/exam/<filename>")
def delete_exam(filename):
    filepath = os.path.join(EXAMS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("list_exams"))


@app.route("/delete/criteria/<filename>")
def delete_criteria(filename):
    filepath = os.path.join(CRITERIA_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("list_criteria"))


@app.route("/delete/review/<filename>")
def delete_review(filename):
    filepath = os.path.join(REVIEWS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("list_reviews"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
