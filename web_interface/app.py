import os
from flask import Flask, render_template, request, flash

from config import SECRET_KEY, EXAMS_DIR, CRITERIA_DIR, REVIEWS_DIR
from routes.main import main_bp
from routes.api import api_bp
from services import ExamEvaluator

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)


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
            selected_batch_criteria = request.form.get("criteria_batch", criteria_files[0])
            try:
                evaluator = ExamEvaluator(CRITERIA_DIR, EXAMS_DIR, REVIEWS_DIR)
                count = evaluator.run_all_reviews(selected_batch_criteria)
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
