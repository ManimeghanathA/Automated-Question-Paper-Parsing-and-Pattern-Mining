# ===============================
# QUESTION EXTRACTION MODULE
# ===============================

import ollama
import json
import re
from pathlib import Path



MODEL_NAME = "qwen2.5:7b"


# -------------------------------
# JSON Extraction Utility
# -------------------------------

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


# -------------------------------
# MAIN QUESTION EXTRACTION
# -------------------------------

def run_question_extraction(raw_text_path: Path, output_dir: Path):

    raw_text_path = Path(raw_text_path)
    output_dir = Path(output_dir)

    if not raw_text_path.exists():
        raise FileNotFoundError(f"OCR file not found: {raw_text_path}")

    with open(raw_text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        raise ValueError("OCR text is empty.")

    # ===============================
    # SYSTEM PROMPT
    # ===============================

    SYSTEM_PROMPT = """
    You are an exam paper reconstruction engine.

    You must:
    - Extract only information present in the text.
    - Never invent completely new questions.
    - You may logically infer missing question numbers only if the sequence is obvious.
    - You may correct minor OCR spelling errors in question text.
    - Never hallucinate marks.
    - Infer marks ONLY if global marking pattern clearly exists.
    - Return STRICT JSON only.
    - Do not explain anything.
    """


    # ===============================
    # FINAL PROMPT
    # ===============================

    FINAL_PROMPT = """
    Reconstruct the exam paper from the OCR text below in a specific format.

    Follow these rules:

    1. Identify the Course Code and Course Title
    2. Identify main questions.
    3. Identify sub-questions (a), (b), (i), etc..., can by in any format
    4. If marks are written next to sub-questions → assign there and compute main question mark accordingly.
    5. If main question mark is explicitly specified → assign it.
    6. Check if there are any signs for number of questions or maximum marks, and construct questions according to that, do not create duplicate questions
    7. If marks cannot be logically derived → set marks as null
    8. Do not invent missing text.
    9. If question numbers are partially missing, infer sequence ONLY if clear.
    10. Ignore OCR garbage, headers, instructions, and answers.
    11. Return STRICT JSON only.
    12. If a main question contains sub-questions (a), (b), (i), etc., then:

    - The main question_text must contain ONLY the shared introductory part (if any).
    - If there is no shared introductory statement, then set question_text as an empty string "".
    - Do NOT duplicate sub-question content inside main question.
    - Do NOT copy the entire main question into sub-questions.
    - Each sub-question must contain ONLY its own specific text.

    13. Avoid redundancy:
    - The same text must not appear in both question_text and sub_questions.
    - Content should exist in exactly one place only.

    14. If there is only 1 sub-question , then keep the sub question empty and we will have that it in the main question itself 

    Return JSON in this format:

    {{
    "course_code": "",
    "course_title": "",
    "questions": [
        {{
        "question_number": "",
        "question_text": "",
        "marks": null,
        "sub_questions": [
            {{
            "sub_question_label": "",
            "text": "",
            "marks": null
            }}
        ]
        }}
    ]
    }}
    """ +  f"""

    OCR TEXT:
    {text}
    """

    print(f"\n🧠 Extracting questions from {raw_text_path.name}...")

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FINAL_PROMPT}
        ],
        options={
            "temperature": 0,
            "top_p": 0.9
        }
    )

    raw_output = response["message"]["content"]
    parsed_json = extract_json_from_text(raw_output)

    if parsed_json is None:
        raise Exception("Model failed to return valid JSON.")

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{raw_text_path.stem}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Structured JSON saved to: {output_path}")

    return output_path