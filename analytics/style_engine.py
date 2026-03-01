# ==========================================================
# FINAL ROBUST STYLE ENGINE (v3.1)
# ==========================================================

import json
import spacy
import re
from pathlib import Path
from collections import defaultdict

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

class RobustStyleEngine:
    def __init__(self):
        # Action-based categories
        self.NUM_VERBS = {"calculate", "compute", "solve", "evaluate", "derive", "find", "determine", "integrate"}
        self.DESC_VERBS = {"explain", "discuss", "describe", "define", "state", "summarize", "outline"}
        self.DIAG_VERBS = {"draw", "sketch", "plot", "label", "diagram", "circuit"}
        self.ANAL_VERBS = {"compare", "contrast", "justify", "analyze", "distinguish", "critique"}

    def get_symbol_density(self, text):
        """Measures math-specific character concentration."""
        # Finds operators, brackets, and units (kg, hz, etc.)
        math_symbols = len(re.findall(r"[\+\=\-\*\/\{\}\[\]\^√πΣΔ]|(?<=\d)(hz|kg|mv|ma|v|w|j|m/s)", text.lower()))
        # Presence of numbers
        digits = len(re.findall(r"\d+", text))
        # Total word count to normalize
        word_count = len(text.split()) + 1
        return (math_symbols + (digits * 0.5)) / word_count

    def classify(self, text):
        doc = nlp(text.lower())
        scores = defaultdict(float)
        
        # 1. Identify the command (ROOT Verb)
        root_verb = next((token.lemma_ for token in doc if token.dep_ == "ROOT"), None)
        
        if root_verb in self.NUM_VERBS: scores["Numerical"] += 5.0
        if root_verb in self.DIAG_VERBS: scores["Diagrammatic"] += 5.0
        if root_verb in self.ANAL_VERBS: scores["Analytical"] += 4.0
        if root_verb in self.DESC_VERBS: scores["Descriptive"] += 3.0

        # 2. Entity Context (filtering out DATES from NUMBERS)
        # Numerical logic: Only count it if it's NOT a Date or Ordinal
        for ent in doc.ents:
            if ent.label_ in ["QUANTITY", "CARDINAL", "PERCENT"]:
                scores["Numerical"] += 1.5
            if ent.label_ in ["DATE", "ORDINAL"]:
                scores["Descriptive"] += 0.5  # Contextual context

        # 3. Density Check
        density = self.get_symbol_density(text)
        if density > 0.25:
            scores["Numerical"] += 4.0
        elif density > 0.1:
            scores["Numerical"] += 1.2

        # 4. Fallback Logic
        if not scores:
            return "Descriptive"
            
        best_style = max(scores, key=scores.get)
        
        # Handle the Bridge (High Math Density + Analytical Intent)
        if scores["Numerical"] > 2.0 and scores["Analytical"] > 2.5:
            return "Applied/Numerical"
            
        return best_style

def compute_style_distribution(mapped_results, course_code, output_dir):
    engine = RobustStyleEngine()
    per_paper_counts = defaultdict(lambda: defaultdict(int))
    total_counts = defaultdict(int)

    for q in mapped_results:
        style = engine.classify(q["text"])
        per_paper_counts[q["paper_name"]][style] += 1
        total_counts[style] += 1

    overall_total = sum(total_counts.values())
    
    output = {
        "course_code": course_code,
        "per_paper_style_distribution": {
            paper: {s: round((c/sum(counts.values()))*100, 2) for s, c in counts.items()}
            for paper, counts in per_paper_counts.items()
        },
        "combined_style_distribution": {
            s: round((c/overall_total)*100, 2) for s, c in total_counts.items()
        }
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"style_analysis_{course_code}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print(f"✅ Success: Analysis for {course_code} saved.")
    return output