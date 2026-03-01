# ===============================
# SUBJECT GATE MODULE
# ===============================

import json
from pathlib import Path


def validate_subject(cleaned_dir: Path, syllabus_course_code: str):
    cleaned_dir = Path(cleaned_dir)

    if not cleaned_dir.exists():
        raise FileNotFoundError("Cleaned JSON directory not found.")

    json_files = list(cleaned_dir.glob("*.json"))

    if not json_files:
        raise ValueError("No cleaned JSON files found.")

    invalid_files = []

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        paper_code = data.get("course_code", "").strip().upper()

        if paper_code != syllabus_course_code.upper():
            invalid_files.append({
                "file_name": file_path.name,
                "paper_code": paper_code
            })

    if invalid_files:
        print("\n❌ SUBJECT MISMATCH DETECTED:")
        for item in invalid_files:
            print(f"File: {item['file_name']} | Code Found: {item['paper_code']}")
        raise Exception("Analytics stopped due to subject mismatch.")

    print("\n✅ Subject validation successful. All papers match syllabus.")