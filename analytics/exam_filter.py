# ===============================
# EXAM RANGE FILTER ENGINE
# ===============================

def filter_mapped_results_by_range(mapped_results, start_module, end_module):
    """
    Filters mapped results based on selected module range.

    Returns:
    - filtered_results (for analytics)
    - out_of_range_results (for optional reporting)
    """

    filtered_results = []
    out_of_range_results = []

    for q in mapped_results:

        in_range_topics = []
        out_range_topics = []

        for t in q["mapped_topics"]:
            module_id = t["module_id"]

            if module_id is None:
                continue

            if start_module <= module_id <= end_module:
                in_range_topics.append(t)
            else:
                out_range_topics.append(t)

        # If at least one topic falls in selected range
        if in_range_topics:
            filtered_results.append({
                **q,
                "mapped_topics": in_range_topics
            })

        # Track completely out-of-range questions
        elif out_range_topics:
            out_of_range_results.append(q)

    return filtered_results, out_of_range_results