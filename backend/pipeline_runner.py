from analytics.data_loader import load_questions
from analytics.topic_mapper import map_questions_to_topics
from analytics.importance_engine import compute_topic_importance
from analytics.grading_engine import compute_grading_distribution
from analytics.style_engine import compute_style_distribution
from analytics.canonical_engine import compute_canonical_questions

def run_pipeline(syllabus_path, cleaned_dir, selected_modules, course_code, output_dir, logger):
    logger(">>[INFO] Loading questions...")
    questions = load_questions(cleaned_dir)

    logger(">>[INFO] Mapping questions to topics...")
    mapped = map_questions_to_topics(questions, selected_modules, course_code)

    logger(">>[INFO] Computing topic importance...")
    importance = compute_topic_importance(mapped, course_code, output_dir)

    logger(">>[INFO] Computing grading distribution...")
    grading = compute_grading_distribution(mapped, course_code, output_dir)

    logger(">>[INFO] Computing style distribution...")
    style = compute_style_distribution(mapped, course_code, output_dir)

    logger(">>[INFO] Computing canonical questions...")
    canonical = compute_canonical_questions(mapped, course_code, output_dir)

    return {
        "importance": importance,
        "grading": grading,
        "style": style,
        "canonical": canonical
    }