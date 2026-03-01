# ===============================
# HIERARCHICAL + CONCEPT-AWARE TOPIC MAPPING
# ===============================

import numpy as np
import re
from collections import Counter
from rapidfuzz import fuzz

from .config import MAX_TOPICS_PER_QUESTION
from .embedding_engine import EmbeddingEngine
from .text_utils import (
    normalize_text,
    extract_acronyms_from_topics,
    expand_acronyms
)

# ===============================
# CONFIGURATION
# ===============================

SEMANTIC_WEIGHT = 0.5
CONCEPT_WEIGHT = 0.4
FUZZY_WEIGHT = 0.1

MODULE_MARGIN = 0.05
TOPIC_MARGIN = 0.03

MIN_CONCEPT_FLOOR = 0.05
MIN_SEMANTIC_FLOOR = 0.20


# ===============================
# TOKENIZATION
# ===============================

STOPWORDS = {
    "the", "is", "and", "of", "in", "to", "a", "for",
    "with", "on", "that", "as", "an", "are", "by",
    "be", "this", "using", "such", "how", "what",
    "which", "explain", "design", "discuss",
    "analyze", "compare", "describe"
}


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    tokens = text.split()
    return [t[:-1] if t.endswith("s") else t
            for t in tokens if t not in STOPWORDS and len(t) > 2]


# ===============================
# ACRONYM EXTRACTION (MAIN + SUB)
# ===============================

def extract_acronyms_from_enriched(selected_modules):

    temp_structure = []

    for module in selected_modules:

        topic_list = []

        for main in module["main_topics"]:
            topic_list.append(main["main_topic"])
            topic_list.extend(main.get("sub_topics", []))

        temp_structure.append({
            "topics": topic_list
        })

    return extract_acronyms_from_topics(temp_structure)


# ===============================
# MODULE SELECTOR
# ===============================

class ModuleSelector:

    def __init__(self, selected_modules, course_title, embedding_engine):

        self.embedding_engine = embedding_engine
        self.module_ids = []
        self.module_embeddings = []

        module_texts = []

        for module in selected_modules:

            module_id = module["module_id"]
            module_name = module["module_name"]

            topic_words = []

            for main in module["main_topics"]:
                topic_words.append(main["main_topic"])
                topic_words.extend(main.get("sub_topics", []))

            structured = f"{course_title} {module_name} {' '.join(topic_words)}"

            module_texts.append(normalize_text(structured))
            self.module_ids.append(module_id)

        self.module_embeddings = self.embedding_engine.encode(module_texts)

    def select_modules(self, question_embedding):

        similarities = np.dot(self.module_embeddings, question_embedding)

        top_score = np.max(similarities)

        selected = []

        for idx, score in enumerate(similarities):
            if score >= top_score - MODULE_MARGIN:
                selected.append((self.module_ids[idx], score))

        return selected


# ===============================
# TOPIC SELECTOR (NEW SCORING)
# ===============================

class TopicSelector:

    def __init__(self, selected_modules, embedding_engine):

        self.embedding_engine = embedding_engine

        self.topic_embeddings = []
        self.topic_metadata = []
        self.topic_token_sets = []

        topic_texts = []

        for module in selected_modules:

            module_id = module["module_id"]

            for main in module["main_topics"]:

                main_topic = main["main_topic"]
                sub_topics = main.get("sub_topics", [])

                # Only main + subtopics (NO description)
                topic_text = f"{main_topic} {' '.join(sub_topics)}"

                topic_texts.append(normalize_text(topic_text))

                self.topic_metadata.append({
                    "module_id": module_id,
                    "topic": main_topic,
                    "sub_topics": sub_topics
                })

                token_set = set(tokenize(topic_text))
                self.topic_token_sets.append(token_set)

        self.topic_embeddings = self.embedding_engine.encode(topic_texts)

    def select_topics(self, question_text, question_embedding, allowed_modules):

        question_tokens = set(tokenize(question_text))

        similarities = np.dot(self.topic_embeddings, question_embedding)

        scored_topics = []

        for idx, semantic_score in enumerate(similarities):

            module_id = self.topic_metadata[idx]["module_id"]

            if module_id not in allowed_modules:
                continue

            if semantic_score < MIN_SEMANTIC_FLOOR:
                continue

            topic_tokens = self.topic_token_sets[idx]

            if not topic_tokens:
                concept_score = 0.0
            else:
                overlap = topic_tokens.intersection(question_tokens)
                concept_score = len(overlap) / len(topic_tokens)

            fuzzy_score = fuzz.token_set_ratio(
                " ".join(topic_tokens),
                question_text
            ) / 100.0

            final_score = (
                SEMANTIC_WEIGHT * semantic_score +
                CONCEPT_WEIGHT * concept_score +
                FUZZY_WEIGHT * fuzzy_score
            )

            scored_topics.append({
                "module_id": module_id,
                "topic": self.topic_metadata[idx]["topic"],
                "confidence": round(float(final_score), 4)
            })

        if not scored_topics:
            return []

        scored_topics = sorted(
            scored_topics,
            key=lambda x: x["confidence"],
            reverse=True
        )

        top_score = scored_topics[0]["confidence"]

        selected = [
            t for t in scored_topics
            if t["confidence"] >= top_score - TOPIC_MARGIN
        ]

        return selected[:MAX_TOPICS_PER_QUESTION]


# ===============================
# MAIN FUNCTION
# ===============================

def map_questions_to_topics(
    questions,
    selected_modules,
    course_title
):

    print("\n🔹 Starting Concept-Aware Hierarchical Mapping...")

    embedding_engine = EmbeddingEngine()

    acronym_dict = extract_acronyms_from_enriched(selected_modules)

    module_selector = ModuleSelector(
        selected_modules,
        course_title,
        embedding_engine
    )

    topic_selector = TopicSelector(
        selected_modules,
        embedding_engine
    )

    enriched_questions = []

    for q in questions:

        original_text = q["text"]

        cleaned_text = normalize_text(original_text)
        expanded_text = expand_acronyms(cleaned_text, acronym_dict)

        question_embedding = embedding_engine.encode(expanded_text)[0]

        # === Module Selection ===
        selected_modules_scored = module_selector.select_modules(question_embedding)
        allowed_module_ids = [m[0] for m in selected_modules_scored]

        # === Topic Selection ===
        selected_topics = topic_selector.select_topics(
            expanded_text,
            question_embedding,
            allowed_module_ids
        )

        # === Fallback (still hierarchical) ===
        if not selected_topics and selected_modules_scored:

            top_module = selected_modules_scored[0][0]

            selected_topics = [{
                "module_id": top_module,
                "topic": "Module-Level Fallback",
                "confidence": 0.30
            }]

        # Allocate marks
        if selected_topics:
            split_marks = q["marks"] / len(selected_topics)
            for t in selected_topics:
                t["allocated_marks"] = split_marks

        enriched_questions.append({
            "paper_name": q["paper_name"],
            "question_number": q["question_number"],
            "text": original_text,
            "marks": q["marks"],
            "mapped_topics": selected_topics
        })

    print("✅ Concept-Aware Mapping Completed.")

    return enriched_questions