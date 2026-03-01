# ===============================
# TOPIC IMPORTANCE ENGINE
# ===============================

import json
from pathlib import Path
from collections import defaultdict
from .config import FREQ_WEIGHT, MARK_WEIGHT


def compute_topic_importance(mapped_results, course_code, output_dir):
    """
    Computes topic importance and saves result internally.
    """

    module_topic_stats = defaultdict(lambda: defaultdict(lambda: {
        "frequency": 0,
        "total_marks": 0,
        "questions": []
    }))

    # ----------------------------
    # Aggregate raw counts
    # ----------------------------
    for q in mapped_results:

        q_id = f"{q['paper_name']} - {q['question_number']}"

        for t in q["mapped_topics"]:
            module_id = t["module_id"]
            topic = t["topic"]

            if topic == "Module-Level Fallback":
                continue

            module_topic_stats[module_id][topic]["frequency"] += 1
            module_topic_stats[module_id][topic]["total_marks"] += t["allocated_marks"]
            module_topic_stats[module_id][topic]["questions"].append(q_id)

    importance_output = {}

    for module_id, topics in module_topic_stats.items():

        max_freq = max(t["frequency"] for t in topics.values())
        max_marks = max(t["total_marks"] for t in topics.values())

        ranked_topics = []

        for topic, stats in topics.items():

            normalized_freq = stats["frequency"] / max_freq if max_freq > 0 else 0
            normalized_marks = stats["total_marks"] / max_marks if max_marks > 0 else 0

            importance_score = (
                FREQ_WEIGHT * normalized_freq +
                MARK_WEIGHT * normalized_marks
            )

            ranked_topics.append({
                "topic": topic,
                "frequency": stats["frequency"],
                "total_marks": round(stats["total_marks"], 2),
                "importance_score": round(importance_score, 4),
                "evidence": stats["questions"]
            })

        ranked_topics.sort(key=lambda x: x["importance_score"], reverse=True)
        importance_output[module_id] = ranked_topics

    # ----------------------------
    # Save internally
    # ----------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"topic_importance_{course_code}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(importance_output, f, indent=4)

    print(f"\n📊 Topic Importance saved to: {file_path}")

    return importance_output