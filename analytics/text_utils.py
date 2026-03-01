# ===============================
# TEXT UTILITY FUNCTIONS
# ===============================

import re
import math
from collections import defaultdict


# -------------------------------
# NORMALIZE TEXT
# -------------------------------

def normalize_text(text: str) -> str:
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # Remove matrix-like numeric rows
        if re.fullmatch(r"[0-9\s\.\-]+", stripped):
            tokens = stripped.split()
            if len(tokens) >= 4:
                continue

        cleaned_lines.append(stripped)

    cleaned_text = " ".join(cleaned_lines)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text.lower().strip()


# -------------------------------
# EXTRACT ACRONYMS
# -------------------------------

def extract_acronyms_from_topics(selected_modules):

    acronym_dict = {}

    for module in selected_modules:
        for topic in module["topics"]:

            # Explicit acronym in parentheses
            match = re.search(r"\(([^)]+)\)", topic)
            if match:
                acronym = match.group(1).strip().upper()
                if 2 <= len(acronym) <= 6:
                    acronym_dict[acronym] = topic

            # Auto-generate acronym from capitalized words
            words = topic.split()
            capital_words = [
                w for w in words
                if w[0].isupper() and w.isalpha()
            ]

            if len(capital_words) >= 2:
                generated = "".join([w[0] for w in capital_words]).upper()
                if 2 <= len(generated) <= 6:
                    acronym_dict[generated] = topic

    return acronym_dict


# -------------------------------
# EXPAND ACRONYMS
# -------------------------------

def expand_acronyms(text: str, acronym_dict: dict):

    words = text.split()
    expanded_words = []

    for word in words:
        clean_word = re.sub(r"[^\w]", "", word).upper()

        if clean_word in acronym_dict:
            full_form = acronym_dict[clean_word]
            expanded_words.append(f"{word} ({full_form})")
        else:
            expanded_words.append(word)

    return " ".join(expanded_words)


# -------------------------------
# BUILD IDF FROM SYLLABUS
# -------------------------------

def build_topic_idf(selected_modules):

    df = defaultdict(int)
    total_topics = 0

    for module in selected_modules:
        for topic in module["topics"]:
            total_topics += 1
            tokens = set(normalize_text(topic).split())
            for token in tokens:
                df[token] += 1

    idf = {}

    for token, freq in df.items():
        idf[token] = math.log((total_topics + 1) / (freq + 1))

    return idf


# -------------------------------
# IDF-WEIGHTED LEXICAL SCORE
# -------------------------------

def compute_weighted_lexical_score(question_text: str,
                                   topic_text: str,
                                   idf_dict: dict):

    q_tokens = set(question_text.split())
    t_tokens = topic_text.split()

    if not t_tokens:
        return 0.0

    weighted_overlap = 0.0
    total_weight = 0.0

    for token in t_tokens:
        weight = idf_dict.get(token, 0.0)
        total_weight += weight

        if token in q_tokens:
            weighted_overlap += weight
        else:
            # partial containment
            for q_word in q_tokens:
                if token in q_word:
                    weighted_overlap += weight * 0.8
                    break

    if total_weight == 0:
        return 0.0

    lexical_score = weighted_overlap / total_weight

    return min(lexical_score, 1.0)