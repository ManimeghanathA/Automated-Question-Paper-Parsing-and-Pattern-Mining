# ===============================
# SUBJECT INTEGRITY GATE MODULE
# ===============================

import ollama
import json
import re
from pathlib import Path


MODEL_NAME = "qwen2.5:7b"


# ===============================
# UTILITIES
# ===============================

def extract_json_from_text(raw_text: str):
    try:
        return json.loads(raw_text)
    except:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
    return None


def call_llm_extract_course(text_snippet):
    SYSTEM_PROMPT = """
    You are a strict information extraction engine.

    Extract only:
    - course_code
    - course_title

    Rules:
    - Extract exactly what appears in text.
    - Make course code alphabets to upper cased
    - Course code has 8 chars, first 4 chars are letters, next 3 chars are numbers and last char is L or P
    - If not found, return empty string "".
    - Return STRICT JSON only.
    - Do not explain anything.
    - Do not hallucinate
    """

    USER_PROMPT = f"""
    Extract the course code and course title.

    Return JSON in this format:

    {{
      "course_code": "",
      "course_title": ""
    }}

    TEXT:
    {text_snippet}
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        options={
            "temperature": 0,
            "top_p": 0.9,
            "num_predict": 150
        }
    )

    return response["message"]["content"]


# ===============================
# MAIN SUBJECT GATE FUNCTION
# ===============================

def validate_papers(raw_text_dir, syllabus_json_path, course_mapping_path):

    raw_text_dir = Path(raw_text_dir)
    syllabus_json_path = Path(syllabus_json_path)
    course_mapping_path = Path(course_mapping_path)

    if not syllabus_json_path.exists():
        raise FileNotFoundError("❌ syllabus.json not found")

    if not course_mapping_path.exists():
        raise FileNotFoundError("❌ course_mapping.json not found")

    with open(syllabus_json_path, "r", encoding="utf-8") as f:
        syllabus_data = json.load(f)

    syllabus_code = syllabus_data.get("course_code", "").strip()

    with open(course_mapping_path, "r", encoding="utf-8") as f:
        course_map = json.load(f)

    print("✅ Syllabus and Mapping loaded.")

    valid_papers = []
    invalid_papers = []

    text_files = list(raw_text_dir.glob("*.txt"))

    if not text_files:
        print("⚠ No raw text files found.")
        return valid_papers, invalid_papers

    for paper_path in text_files:

        print(f"\n🔎 Checking paper: {paper_path.name}")

        with open(paper_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        snippet = raw_text[:500]

        raw_output = call_llm_extract_course(snippet)
        parsed = extract_json_from_text(raw_output)

        if parsed is None:
            print("❌ Failed to parse LLM output.")
            invalid_papers.append({
                "file_name": paper_path.name,
                "path": str(paper_path)
            })
            continue

        paper_code = re.sub(r"\s+", "", parsed.get("course_code", "")).upper()
        paper_title = parsed.get("course_title", "").strip()

        print(f"Detected Code: {paper_code}")
        print(f"Detected Title: {paper_title}")

        # -------------------------------
        # HANDLE MISSING TITLE
        # -------------------------------

        if paper_code and not paper_title:
            if paper_code in course_map:
                paper_title = course_map[paper_code]
                print("ℹ Filled missing title using course mapping.")

        # -------------------------------
        # HANDLE MISSING CODE (MULTI MATCH SAFE)
        # -------------------------------

        if paper_title and not paper_code:

            possible_codes = [
                code for code, title in course_map.items()
                if title.lower() == paper_title.lower()
            ]

            if len(possible_codes) == 0:
                print("⚠ No matching course codes found for title.")

            elif len(possible_codes) == 1:
                paper_code = possible_codes[0]
                print("ℹ Single matching code found from title.")

            else:
                print(f"ℹ Multiple matching codes found: {possible_codes}")

                if syllabus_code in possible_codes:
                    paper_code = syllabus_code
                    print("ℹ Matched syllabus course code among multiple matches.")
                else:
                    print("⚠ Multiple matches found, but none match syllabus.")
                    paper_code = ""

        # -------------------------------
        # FINAL VALIDATION
        # -------------------------------

        print(f"Final Code Used: {paper_code}")
        print(f"Syllabus Code: {syllabus_code}")

        if paper_code == syllabus_code:
            print("✅ Valid paper")
            valid_papers.append({
                "file_name": paper_path.name,
                "path": str(paper_path)
            })
        else:
            print("❌ Invalid paper (subject mismatch)")
            invalid_papers.append({
                "file_name": paper_path.name,
                "path": str(paper_path)
            })

    # -------------------------------
    # SUMMARY
    # -------------------------------

    print("\n" + "=" * 30)
    print(f"RESULTS: {len(valid_papers)} Valid, {len(invalid_papers)} Invalid")
    print("=" * 30)

    if invalid_papers:
        print("\n❌ THE FOLLOWING PAPERS ARE INVALID:")
        for i in invalid_papers:
            print(f"- {i['file_name']}")
    else:
        print("\n🚀 All papers validated.")

    return valid_papers, invalid_papers