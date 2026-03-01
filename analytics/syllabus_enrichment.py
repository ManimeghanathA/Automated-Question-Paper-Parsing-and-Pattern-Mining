import json
from pathlib import Path
import ollama
import wikipedia
import re

MODEL_NAME = "qwen2.5:7b"

def normalize_topic(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)  # remove special chars
    text = re.sub(r"\s+", " ", text).strip()  # collapse spaces
    return text


def get_or_create_enriched_syllabus(syllabus_json_path: Path, enriched_dir: Path):

    syllabus_json_path = Path(syllabus_json_path)
    enriched_dir = Path(enriched_dir)

    with open(syllabus_json_path, "r", encoding="utf-8") as f:
        syllabus_data = json.load(f)

    course_code = syllabus_data["course_code"]
    course_title = syllabus_data["course_title"]

    enriched_dir.mkdir(parents=True, exist_ok=True)

    enriched_path = enriched_dir / f"enriched_{course_code}.json"

    # 🔥 If already exists → return
    if enriched_path.exists():
        print(f"✅ Enriched syllabus found for {course_code}. Loading existing.")
        return enriched_path

    print(f"🚀 Building enriched syllabus for {course_code}...")

    enriched_modules = []

    for module in syllabus_data["modules"]:
        if not module["topics"]:
            print(f"Skipping module {module['module_id']} (no topics).")
            continue
        enriched_module = restructure_module_with_llm(module)
        enriched_modules.append(enriched_module)

    enriched_output = {
        "course_code": course_code,
        "course_title": course_title,
        "modules": enriched_modules
    }

    with open(enriched_path, "w", encoding="utf-8") as f:
        json.dump(enriched_output, f, indent=2, ensure_ascii=False)

    print(f"✅ Enriched syllabus saved to: {enriched_path}")

    return enriched_path



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

def restructure_module_with_llm(module):

    module_id = module["module_id"]
    module_name = module["module_name"]
    topics = module["topics"]

    system_prompt = """
        ### Role
        You are a Syllabus Logic Engine. Your sole purpose is to transform a flat list of topics into a strictly hierarchical JSON structure.

        ### Constraints
        You are a deterministic syllabus restructuring engine.

        You MUST process topics sequentially in the given order.

        For each topic, decide:

        - Either it remains an independent Main Topic.
        - Or it becomes a Sub-topic of a PRECEDING topic only.
        
        For Every Main Topic:
        - write a descritpion about the main topic for 2  lines

        For every main and sub topic:
        - Append the acronym at the end if they have one

        STRICT RULES:

        1. Use ONLY the provided topics.
        2. Do NOT invent new topics.
        3. Every topic must appear exactly once.
        4. A Main Topic cannot also appear as a Sub-topic.
        5. A topic can only be assigned under a topic that appears BEFORE it.
        6. Do NOT redesign the syllabus conceptually.
        7. Prefer minimal restructuring.
        8. Maintain structural balance.
        9. The number of Main Topics must be at most 50% of total topics.
        10. Each Main Topic can have at most 4 subtopics.
        11. For Every main and sub topic, Append the acronym at the end if they have one
        12. If unsure, keep topic as Main Topic.
        13. Only one level of hierarchy is allowed. 
        14. Sub Topis should be Plain list of strings
        15. Write a concise 2 line explanation of the selected main topic strictly within the context of  syllabus.
        16. Do not introduce unrelated fields. Be precise and technical.
        17. Return plain text in desc and for main topic only.
        18. All the topics Provided MUST be included, no topic should be ignored.
        19. Return STRICT JSON only.
        20. Do not explain.

    """

    user_prompt = f"""
    Module Name: {module_name}

    Topics:
    {", ".join(topics)}

    ### Output Format
    - Return STRICT JSON only.
    - No markdown wrappers (no ```json).
    - No conversational filler or explanations.

    ### Schema

    {{
      "main_topics": [
        {{
          "main_topic": "",
          "sub_topics": [],
          "desc" : " "
        }}
      ]
    }}
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0}
    )

    raw_output = response["message"]["content"]

    if raw_output is None:
        raise Exception("❌ LLM did not return valid JSON.")
    print(raw_output)

    structured = extract_json_from_text(raw_output)


    if structured is None:
        print("RAW OUTPUT FROM OLLAMA:")
        print(raw_output)
        raise Exception("❌ LLM did not return valid JSON.")

    # 🔥 VALIDATE
    returned_topics = set()
    for main in structured["main_topics"]:
        returned_topics.add(main["main_topic"])
        for sub in main["sub_topics"]:
            returned_topics.add(sub)


    return {
        "module_id": module_id,
        "module_name": module_name,
        "main_topics": structured["main_topics"]
    }