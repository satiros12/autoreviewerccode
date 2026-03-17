import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXAMS_DIR = os.path.join(BASE_DIR, "exams")
ANNOTATED_EXAMS_DIR = os.path.join(BASE_DIR, "annotated_exams")
CRITERIA_DIR = os.path.join(BASE_DIR, "criteria")
CRITERIA_DB_DIR = os.path.join(BASE_DIR, "criteria_db")
REVIEWS_DIR = os.path.join(BASE_DIR, "reviews")

for directory in [EXAMS_DIR, ANNOTATED_EXAMS_DIR, CRITERIA_DIR, CRITERIA_DB_DIR, REVIEWS_DIR]:
    os.makedirs(directory, exist_ok=True)

ALLOWED_EXTENSIONS = {"c", "json"}

SECRET_KEY = "cexams-secret-key-change-in-production"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "deepseek/deepseek-chat"
