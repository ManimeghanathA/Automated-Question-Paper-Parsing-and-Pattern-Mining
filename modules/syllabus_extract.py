# ===============================
# SYLLABUS EXTRACTION MODULE
# ===============================

import re
import json
import fitz
from pathlib import Path
import os



# -------------------------------
# MAIN FUNCTION
# -------------------------------

def parse_syllabus_pdf(pdf_path: Path, output_dir: Path):

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Syllabus PDF not found: {pdf_path}")

    print(f"\n📘 Parsing syllabus: {pdf_path.name}")

    # -------------------------------
    # READ PDF
    # -------------------------------

    doc = fitz.open(pdf_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    doc.close()

    raw_text = raw_text.split("Text Book(s)")[0]
    raw_text = raw_text.split("Text Book")[0]

    # -------------------------------
    # EXTRACT COURSE CODE & TITLE
    # -------------------------------

    short_pattern = re.search(
        r"(B[A-Z]{3,5}\d{3}[L|P])\s+([\w\s]+?)(?=\s*[\(\d])",
        raw_text
    )

    table_code = re.search(
        r"Course code\s*\n\s*(B[A-Z]{3,5}\d{3}[L|P])",
        raw_text,
        re.IGNORECASE
    )

    table_title = re.search(
        r"Course Title\s*\n\s*([\w\s]+?)(?=\n\s*LTPC|\n\s*Syllabus)",
        raw_text,
        re.IGNORECASE
    )

    if table_code and table_title:
        course_code = table_code.group(1).strip()
        course_title = table_title.group(1).strip()
    elif short_pattern:
        course_code = short_pattern.group(1).strip()
        course_title = short_pattern.group(2).strip()
    else:
        raise ValueError("Could not extract course code/title from syllabus.")
    course_code = "".join(course_code.split())

    print(f"Course Code: {course_code}")
    print(f"Course Title: {course_title}")

    # -------------------------------
    # ISOLATE MODULE TABLE
    # -------------------------------

    start_match = re.search(r"Module\s*:\s*\d+", raw_text, re.IGNORECASE)
    end_match = re.search(r"Total\s+Lecture\s+Hours?", raw_text, re.IGNORECASE | re.MULTILINE)

    if not start_match or not end_match:
        raise ValueError("Module table boundaries not found.")

    table_text = raw_text[start_match.start():end_match.start()]

    parts = re.split(r"(Module\s*:\s*\d+)", table_text, flags=re.IGNORECASE)

    module_blocks = []
    for i in range(1, len(parts), 2):
        if i + 1 > len(parts):
            break
        header_token = parts[i].strip()
        body = parts[i + 1].strip()
        module_blocks.append((header_token, body))

    # -------------------------------
    # DELIMITERS
    # -------------------------------

    EN_DASH = "\u2013"
    TOPIC_DELIMITER_RE = re.compile(
        r"\s+[" + EN_DASH + r"-]\s+|,\s+"
    )
    HOURS_RE = re.compile(r"\b\d+\s*hours?\b", re.IGNORECASE)

    def clean_topic(s):
        s = s.strip()
        s = s.strip(EN_DASH + "-,\t ")
        s = re.sub(r"\s+", " ", s).strip()
        if not s or len(s) < 2:
            return None
        if s.isdigit():
            return None
        if HOURS_RE.fullmatch(s):
            return None
        return s

    def extract_topics(body: str):
        line = " ".join(body.splitlines())
        line = re.sub(r"\s+", " ", line).strip()
        raw_parts = TOPIC_DELIMITER_RE.split(line)
        topics = []
        seen = set()
        for p in raw_parts:
            t = clean_topic(p)
            if t is None:
                continue
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            topics.append(t)
        return topics

    # -------------------------------
    # BUILD SYLLABUS STRUCTURE
    # -------------------------------

    syllabus = []

    for header_token, body in module_blocks:

        mid_match = re.search(r"Module\s*:\s*(\d+)", header_token, re.IGNORECASE)
        if not mid_match:
            continue

        module_id = int(mid_match.group(1))

        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]

        if not lines:
            syllabus.append({
                "module_id": module_id,
                "module_name": "",
                "topics": []
            })
            continue

        first_line = HOURS_RE.sub("", lines[0]).strip()
        module_name = first_line.strip(EN_DASH + "-,\t ").strip()

        topic_body = " ".join(lines[1:]) if len(lines) > 1 else ""
        topic_body = HOURS_RE.sub("", topic_body)
        topic_body = re.sub(r"\s+", " ", topic_body).strip()

        topics = extract_topics(topic_body)

        syllabus.append({
            "module_id": module_id,
            "module_name": module_name,
            "topics": topics,
        })

    print(f"Modules parsed: {len(syllabus)}")

    # -------------------------------
    # SAVE JSON
    # -------------------------------

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"syllabus_modules_{course_code}.json"

    output = {
        "course_code": course_code,
        "course_title": course_title,
        "modules": syllabus,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Syllabus saved to: {out_path}")

    return out_path