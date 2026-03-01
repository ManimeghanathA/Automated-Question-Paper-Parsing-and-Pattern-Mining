# ===============================
# JSON CLEANING & MARK ENGINE
# ===============================

import json
import re
from pathlib import Path


# =========================================================
# ------------------ STRUCTURE UTILITIES ------------------
# =========================================================

def remove_empty_subquestions(question):
    subs = question.get("sub_questions", []) or []
    question["sub_questions"] = [
        s for s in subs if (s.get("text") or "").strip() != ""
    ]
    return question


def move_single_sub_to_main(question):
    subs = question.get("sub_questions", [])

    if (
        (question.get("question_text") or "").strip() == ""
        and len(subs) == 1
    ):
        question["question_text"] = subs[0]["text"]
        question["marks"] = subs[0].get("marks")
        question["sub_questions"] = []

    return question


def remove_duplication_between_main_and_sub(question):
    main_text = (question.get("question_text") or "").strip()
    subs = question.get("sub_questions", [])

    for s in subs:
        sub_text = (s.get("text") or "").strip()
        if sub_text and sub_text in main_text:
            main_text = main_text.replace(sub_text, "").strip()

    question["question_text"] = main_text
    return question


def fix_duplicate_question_numbers(questions):
    seen = set()
    max_number = 0

    # Find max numeric question number
    for q in questions:
        qn = q.get("question_number", "")
        if str(qn).isdigit():
            max_number = max(max_number, int(qn))

    for q in questions:
        qn = q.get("question_number", "")
        if qn in seen:
            max_number += 1
            q["question_number"] = str(max_number)
        else:
            seen.add(qn)

    return questions

def load_syllabus_metadata(syllabus_json_path):
    with open(syllabus_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("course_code"), data.get("course_title")


# =========================================================
# ------------------ MARK ENGINE --------------------------
# =========================================================

def determine_expected_total(total_questions):
    if total_questions > 7:
        return 100
    else:
        return 50


def apply_global_mark_distribution(questions, expected_total):

    total_questions = len(questions)

    null_questions = [q for q in questions if q.get("marks") is None]
    null_count = len(null_questions)

    if total_questions == 0:
        return questions

    null_ratio = null_count / total_questions

    # -----------------------------------
    # CASE 1: > 40% null
    # -----------------------------------
    if null_ratio > 0.4:
        equal_mark = expected_total // total_questions
        for q in questions:
            if (q.get("question_text") or "").strip():
                q["marks"] = equal_mark
        return questions

    # -----------------------------------
    # CASE 2: ≤ 40% null
    # -----------------------------------
    existing_sum = sum([q.get("marks") or 0 for q in questions])
    remaining = expected_total - existing_sum

    if remaining > 0 and null_count > 0:
        share = remaining // null_count

        for q in questions:
            if q.get("marks") is None:
                q["marks"] = max(5, share)

    return questions


# =========================================================
# ------------- SUB QUESTION NORMALIZATION ----------------
# =========================================================
def normalize_sub_questions(question):

    subs = question.get("sub_questions", [])
    
    if not subs:
        return question

    # -------------------------------
    # Step 1: Assign 5 to null or zero sub-marks
    # -------------------------------
    for s in subs:
        if s.get("marks") is None or s.get("marks") == 0:
            s["marks"] = 5

    # -------------------------------
    # Step 2: Recompute main marks
    # -------------------------------
    total_sub_marks = sum(s.get("marks", 0) for s in subs)
    question["marks"] = total_sub_marks

    return question

# =========================================================
# ------------------ MAIN PROCESSOR -----------------------
# =========================================================

def process_paper(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get("questions", [])

    # -------------------------------------
    # STRUCTURE CLEANING
    # -------------------------------------
    cleaned_questions = []

    for q in questions:
        q = remove_empty_subquestions(q)
        q = move_single_sub_to_main(q)
        q = remove_duplication_between_main_and_sub(q)
        cleaned_questions.append(q)

    cleaned_questions = fix_duplicate_question_numbers(cleaned_questions)

    # -------------------------------------
    # GLOBAL MARK DISTRIBUTION
    # -------------------------------------
    expected_total = determine_expected_total(len(cleaned_questions))
    cleaned_questions = apply_global_mark_distribution(
        cleaned_questions,
        expected_total
    )

    # -------------------------------------
    # SUB-QUESTION NORMALIZATION
    # -------------------------------------
    for q in cleaned_questions:
        q = normalize_sub_questions(q)

        # If weird case (no marks assigned but valid text)
        if q.get("marks") is None and (q.get("question_text") or "").strip():
            q["marks"] = 10

    data["questions"] = cleaned_questions

    return data


# =========================================================
# ------------- PIPELINE ENTRY FUNCTION -------------------
# =========================================================

def clean_all_papers(structured_dir: Path, output_dir: Path, syllabus_json_path: Path):

    structured_dir = Path(structured_dir)
    output_dir = Path(output_dir)

    syllabus_code, syllabus_title = load_syllabus_metadata(syllabus_json_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(structured_dir.glob("*.json"))

    for file_path in json_files:
        print(f"🚀 Cleaning & normalizing: {file_path.name}")

        processed = process_paper(file_path)

        # 🔥 FORCE ASSIGN METADATA
        processed["course_code"] = syllabus_code
        processed["course_title"] = syllabus_title

        output_file = output_dir / f"cleaned_{file_path.name}"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved cleaned file: {output_file}")