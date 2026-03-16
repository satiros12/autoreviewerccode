from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
    flash,
)
from werkzeug.utils import secure_filename
import os
import json

from config import EXAMS_DIR, CRITERIA_DIR, REVIEWS_DIR, ALLOWED_EXTENSIONS
from services import ExamEvaluator

main_bp = Blueprint("main", __name__)


def allowed_file(filename, allowed_extensions=ALLOWED_EXTENSIONS):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@main_bp.route("/")
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


@main_bp.route("/upload/exams", methods=["POST"])
def upload_exams():
    if "files[]" not in request.files:
        flash("No files selected", "error")
        return redirect(url_for("main.index"))

    files = request.files.getlist("files[]")
    uploaded = 0
    for file in files:
        if file and allowed_file(file.filename, {"c"}):
            filename = secure_filename(file.filename)
            file.save(os.path.join(EXAMS_DIR, filename))
            uploaded += 1

    flash(f"Uploaded {uploaded} exam files", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/upload/criteria", methods=["POST"])
def upload_criteria():
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    file = request.files["file"]
    if file and allowed_file(file.filename, {"json"}):
        filename = secure_filename(file.filename)
        file.save(os.path.join(CRITERIA_DIR, filename))
        flash(f"Uploaded criteria: {filename}", "success")

    return redirect(url_for("main.index"))


@main_bp.route("/exams")
def list_exams():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    return render_template("exams.html", exam_files=exam_files)


@main_bp.route("/exam/<path:filename>")
def view_exam(filename):
    filepath = os.path.join(EXAMS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return render_template("exam_view.html", filename=filename, content=content)
    return "File not found", 404


@main_bp.route("/criteria")
def list_criteria():
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])
    return render_template("criteria_list.html", criteria_files=criteria_files)


@main_bp.route("/criteria/<filename>")
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


@main_bp.route("/criteria/<filename>/save", methods=["POST"])
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

    return redirect(url_for("main.view_criteria", filename=filename))


@main_bp.route("/reviews")
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


@main_bp.route("/review/<filename>")
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


@main_bp.route("/review/<filename>/download")
def download_review(filename):
    return send_from_directory(REVIEWS_DIR, secure_filename(filename), as_attachment=True)


@main_bp.route("/run")
def run_review_page():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DIR) if f.endswith(".json")])

    return render_template(
        "run_review.html",
        exam_files=exam_files,
        criteria_files=criteria_files,
        selected_exam=None,
        selected_criteria=None,
        result=None,
        error=None,
    )


@main_bp.route("/delete/exam/<filename>")
def delete_exam(filename):
    filepath = os.path.join(EXAMS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("main.list_exams"))


@main_bp.route("/delete/criteria/<filename>")
def delete_criteria(filename):
    filepath = os.path.join(CRITERIA_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("main.list_criteria"))


@main_bp.route("/delete/review/<filename>")
def delete_review(filename):
    filepath = os.path.join(REVIEWS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("main.list_reviews"))


@main_bp.route("/reviewer")
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
