# ===============================
# MODULE-WISE GRADING DISTRIBUTION ENGINE
# ===============================

import json
from pathlib import Path
from collections import defaultdict


def compute_grading_distribution(mapped_results, course_code, output_dir):

    paper_module_marks = defaultdict(lambda: defaultdict(float))
    paper_total_marks = defaultdict(float)

    # ----------------------------
    # Aggregate marks per paper
    # ----------------------------
    for q in mapped_results:

        paper = q["paper_name"]

        for t in q["mapped_topics"]:
            module_id = t["module_id"]
            allocated = t["allocated_marks"]

            if module_id is None:
                continue

            paper_module_marks[paper][module_id] += allocated
            paper_total_marks[paper] += allocated

    per_paper_distribution = {}

    for paper, modules in paper_module_marks.items():

        total_marks = paper_total_marks[paper]
        module_percentages = {}

        for module_id, marks in modules.items():
            percentage = (marks / total_marks) * 100 if total_marks > 0 else 0
            module_percentages[module_id] = round(percentage, 2)

        per_paper_distribution[paper] = module_percentages

    # ----------------------------
    # Combined average
    # ----------------------------
    combined_totals = defaultdict(float)
    combined_marks = 0

    for paper, modules in paper_module_marks.items():
        for module_id, marks in modules.items():
            combined_totals[module_id] += marks
            combined_marks += marks

    combined_distribution = {}

    for module_id, marks in combined_totals.items():
        percentage = (marks / combined_marks) * 100 if combined_marks > 0 else 0
        combined_distribution[module_id] = round(percentage, 2)

    grading_output = {
        "per_paper_distribution": per_paper_distribution,
        "combined_average_distribution": combined_distribution
    }

    # ----------------------------
    # Save internally
    # ----------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"grading_distribution_{course_code}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(grading_output, f, indent=4)

    print(f"\n📈 Grading Distribution saved to: {file_path}")

    return grading_output