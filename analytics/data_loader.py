# ===============================
# DATA LOADER MODULE
# ===============================

import json
from pathlib import Path


# -------------------------------
# LOAD SYLLABUS
# -------------------------------

def load_syllabus(syllabus_path: Path):
    syllabus_path = Path(syllabus_path)

    if not syllabus_path.exists():
        raise FileNotFoundError("Syllabus JSON not found.")

    with open(syllabus_path, "r", encoding="utf-8") as f:
        syllabus = json.load(f)

    course_code = syllabus.get("course_code", "").strip()
    modules = syllabus.get("modules", [])

    if not modules:
        raise ValueError("No modules found in syllabus.")

    # Exclude empty modules (e.g., guest lecture module)
    effective_modules = [
        m for m in modules if m.get("topics") and len(m["topics"]) > 0
    ]

    if not effective_modules:
        raise ValueError("No valid modules with topics found in syllabus.")

    max_valid_module = max(m["module_id"] for m in effective_modules)

    return {
        "course_code": course_code,
        "course_title": syllabus["course_title"],
        "modules": effective_modules,
        "max_valid_module": max_valid_module
    }


# -------------------------------
# LOAD CLEANED QUESTION FILES
# -------------------------------

def load_questions(cleaned_dir: Path):
    cleaned_dir = Path(cleaned_dir)

    if not cleaned_dir.exists():
        raise FileNotFoundError("Cleaned JSON directory not found.")

    json_files = list(cleaned_dir.glob("*.json"))

    if not json_files:
        raise ValueError("No cleaned JSON files found.")

    unified_questions = []

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        paper_name = file_path.name
        questions = data.get("questions", [])

        for q in questions:
            main_text = q.get("question_text", "").strip()
            main_marks = q.get("marks", 0)
            question_number = q.get("question_number", "").strip()

            sub_questions = q.get("sub_questions", [])

            # If there are valid sub-questions, treat each as independent unit
            valid_subs = [s for s in sub_questions if s.get("text")]

            if valid_subs:
                for sub in valid_subs:
                    unified_questions.append({
                        "paper_name": paper_name,
                        "question_number": f"{question_number}_{sub.get('sub_question_label','').strip()}",
                        "text": sub.get("text", "").strip(),
                        "marks": sub.get("marks", 0)
                    })
            else:
                unified_questions.append({
                    "paper_name": paper_name,
                    "question_number": question_number,
                    "text": main_text,
                    "marks": main_marks
                })

    return unified_questions