import json
import os

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS, CRITERIA_DB_DIR, EXAMS_DIR, REVIEWS_DIR

main_bp = Blueprint("main", __name__)


def allowed_file(filename, allowed_extensions=ALLOWED_EXTENSIONS):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@main_bp.route("/")
def index():
    exam_files = [f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")]
    criteria_files = [f for f in os.listdir(CRITERIA_DB_DIR) if f.endswith(".json")]
    review_files = [f for f in os.listdir(REVIEWS_DIR) if f.endswith(".json")]

    criteria_list = []
    for cf in criteria_files:
        filepath = os.path.join(CRITERIA_DB_DIR, cf)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        criteria_list.append(
            {
                "filename": cf,
                "titulo": data.get("titulo", cf),
                "nota_maxima": data.get("nota_maxima", 0),
            }
        )

    return render_template(
        "index.html",
        exam_count=len(exam_files),
        criteria_count=len(criteria_files),
        review_count=len(review_files),
        exam_files=sorted(exam_files),
        criteria_list=sorted(criteria_list, key=lambda x: x["titulo"]),
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
        try:
            content = file.read().decode("utf-8")
            criteria_data = json.loads(content)

            criteria_list = []
            if isinstance(criteria_data, dict):
                criteria_list = [criteria_data]
            elif isinstance(criteria_data, list):
                criteria_list = criteria_data
            else:
                flash("Invalid criteria format: expected object or array", "error")
                return redirect(url_for("main.index"))

            saved_count = 0
            updated_count = 0
            for criteria in criteria_list:
                titulo = criteria.get("titulo", "untitled")
                safe_name = secure_filename(titulo)[:100]
                if not safe_name:
                    safe_name = "untitled"

                criteria_file = os.path.join(CRITERIA_DB_DIR, f"{safe_name}.json")
                is_update = os.path.exists(criteria_file)

                with open(criteria_file, "w", encoding="utf-8") as f:
                    json.dump(criteria, f, indent=2, ensure_ascii=False)

                if is_update:
                    updated_count += 1
                else:
                    saved_count += 1

            msg = (
                f"Loaded {len(criteria_list)} criteria ({saved_count} new, {updated_count} updated)"
            )
            flash(msg, "success")
        except json.JSONDecodeError as e:
            flash(f"Invalid JSON: {str(e)}", "error")
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "error")

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


@main_bp.route("/delete/exam/<filename>")
def delete_exam(filename):
    filepath = os.path.join(EXAMS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted exam: {filename}", "success")
    return redirect(url_for("main.list_exams"))


@main_bp.route("/delete/exams-all", methods=["POST"])
def delete_all_exams():
    count = 0
    for f in os.listdir(EXAMS_DIR):
        if f.endswith(".c"):
            os.remove(os.path.join(EXAMS_DIR, f))
            count += 1
    flash(f"Deleted {count} exams", "success")
    return redirect(url_for("main.list_exams"))


@main_bp.route("/criteria")
def list_criteria():
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DB_DIR) if f.endswith(".json")])

    criteria_list = []
    for cf in criteria_files:
        filepath = os.path.join(CRITERIA_DB_DIR, cf)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        criteria_list.append(
            {
                "filename": cf,
                "titulo": data.get("titulo", cf),
                "descripcion": data.get("descripcion", ""),
                "nota_maxima": data.get("nota_maxima", 0),
                "subapartados": data.get("subapartados", []),
            }
        )

    return render_template(
        "criteria_list.html", criteria_list=sorted(criteria_list, key=lambda x: x["titulo"])
    )


@main_bp.route("/criteria/<path:filename>")
def view_criteria(filename):
    filepath = os.path.join(CRITERIA_DB_DIR, secure_filename(filename))
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
    filepath = os.path.join(CRITERIA_DB_DIR, secure_filename(filename))
    new_content = request.form.get("content")

    try:
        json.loads(new_content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        flash("Criteria saved successfully", "success")
    except json.JSONDecodeError as e:
        flash(f"Invalid JSON: {str(e)}", "error")

    return redirect(url_for("main.view_criteria", filename=filename))


@main_bp.route("/delete/criteria/<filename>")
def delete_criteria(filename):
    filepath = os.path.join(CRITERIA_DB_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted criteria: {filename}", "success")
    return redirect(url_for("main.list_criteria"))


@main_bp.route("/delete/criteria-all", methods=["POST"])
def delete_all_criteria():
    count = 0
    for f in os.listdir(CRITERIA_DB_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(CRITERIA_DB_DIR, f))
            count += 1
    flash(f"Deleted {count} criteria", "success")
    return redirect(url_for("main.list_criteria"))


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


@main_bp.route("/review/<filename>/download-text")
def download_review_text(filename):
    filepath = os.path.join(REVIEWS_DIR, secure_filename(filename))
    if not os.path.exists(filepath):
        return "Review not found", 404

    with open(filepath, "r", encoding="utf-8") as f:
        review = json.load(f)

    exam_name = review.get("exam_name", filename)
    overall_score = review.get("overall_score", 0)
    max_score = review.get("maximum_possible_score", 0)

    lines = []
    lines.append(f"Exam: {exam_name}")
    lines.append(f"General Grade: {overall_score}/{max_score}")
    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    for i, eval_item in enumerate(review.get("criteria_evaluations", []), 1):
        criteria_title = eval_item.get("criteria_title", f"Criteria {i}")
        awarded = eval_item.get("awarded_score", 0)
        maximum = eval_item.get("maximum_score", 0)
        justification = eval_item.get("justification", "No justification provided")

        lines.append(f"Criteria {i}: {criteria_title}")
        lines.append(f"Grade: {awarded}/{maximum}")
        lines.append("")
        lines.append("Explanation:")
        lines.append(justification)
        lines.append("")
        lines.append("-" * 50)
        lines.append("")

    text_content = "\n".join(lines)

    from flask import Response

    response = Response(text_content, mimetype="text/plain; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename={exam_name}_review.txt"
    return response


@main_bp.route("/delete/review/<filename>")
def delete_review(filename):
    filepath = os.path.join(REVIEWS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("main.list_reviews"))


@main_bp.route("/delete/reviews-all", methods=["POST"])
def delete_all_reviews():
    count = 0
    for f in os.listdir(REVIEWS_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(REVIEWS_DIR, f))
            count += 1
    flash(f"Deleted {count} reviews", "success")
    return redirect(url_for("main.list_reviews"))


@main_bp.route("/reviewer")
def reviewer():
    exam_files = sorted([f for f in os.listdir(EXAMS_DIR) if f.endswith(".c")])
    criteria_files = sorted([f for f in os.listdir(CRITERIA_DB_DIR) if f.endswith(".json")])

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
