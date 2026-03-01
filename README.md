# Automated Question Paper Parsing and Pattern Mining

## TL;DR

An end-to-end, syllabus-constrained exam analytics system that transforms Previous Year Question Papers (PYQs) into structured, evidence-backed preparation insights.

Instead of guessing what to study, students can:

- Identify the most important topics based on historical marks and frequency  
- Analyze module-wise grading distribution  
- Detect repeated canonical questions across years  
- Understand exam style trends (numerical vs descriptive)  
- Filter analytics based on exam type (CAT-1, CAT-2, FAT)  

Built using semantic embeddings, clustering, OCR, and strict syllabus alignment.

---

## Problem Statement

University exam preparation is often driven by intuition, incomplete resources, or peer suggestions. Students typically:

- Study the entire syllabus without knowing topic importance  
- Miss frequently repeated questions  
- Misjudge module weightage  
- Experience uncertainty before exams  

Although previous year question papers are available, there is no structured mechanism to analyze them in alignment with the official syllabus.

This project addresses that gap by converting exam history into structured intelligence.

---

## Solution Overview

The system performs the following steps:

1. Parses official syllabus documents  
2. Extracts structured questions from raw PDFs  
3. Maps questions to syllabus-defined topics  
4. Detects repetition patterns  
5. Computes importance metrics using marks and frequency  
6. Generates exam-specific filtered analytics  

Every output is traceable to actual question references.  
No hallucinated insights. No uncontrolled topic modeling.

---

## System Architecture

```
Raw Inputs
│
├── Syllabus PDF
└── Question Paper PDFs
        │
        ▼
1. Syllabus Parsing
   - Extract modules and topics
   - Structured JSON generation

2. Syllabus Enrichment
   - Hierarchical restructuring (main + sub-topics)
   - Strict non-invention rules

3. OCR Engine
   - Scanned PDF → Machine-readable text

4. Subject Integrity Gate
   - Course code validation
   - Cross-subject contamination prevention

5. Question Reconstruction
   - LLM-based structured extraction
   - Marks and sub-question preservation

6. JSON Cleaning & Mark Engine
   - Deduplication
   - Mark normalization
   - Sub-question restructuring

7. Topic Mapping Engine
   - SentenceTransformer embeddings
   - Concept token overlap
   - Fuzzy matching
   - Hierarchical module selection
   - Confidence scoring
   - Mark allocation splitting

8. Exam-Range Filtering
   - CAT-1 / CAT-2 / FAT module segmentation
   - Mapping separated from analytics view

9. Analytics Layer
   - Topic importance ranking
   - Module-wise grading distribution
   - Canonical question clustering
   - Question style classification
```

---

## Core Components

### Syllabus-Constrained Topic Mapping

Questions are mapped strictly within official syllabus boundaries.

Mapping uses a weighted combination of:

- Semantic similarity (SentenceTransformers)  
- Concept overlap scoring  
- Fuzzy lexical similarity  

This prevents uncontrolled topic drift and ensures academic defensibility.

---

### Topic Importance Engine

Each topic receives an importance score calculated using:

Importance = (Normalized Frequency × Weight) + (Normalized Marks × Weight)

This ensures high-weightage topics are prioritized even if asked fewer times.

---

### Canonical Question Detection

Semantically similar questions across different years are clustered using:

- Normalized embeddings  
- Agglomerative clustering  
- Medoid-based representative selection  

This identifies repeated conceptual patterns even when phrased differently.

---

### Module-Wise Grading Distribution

Marks are allocated proportionally to mapped topics, allowing accurate computation of:

- Per-paper module distribution  
- Combined average distribution across years  

---

### Question Style Classification

Each question is classified into categories such as:

- Numerical  
- Descriptive  
- Analytical  
- Diagrammatic  
- Applied/Numerical  

Classification is based on:

- Root verb extraction  
- Entity recognition  
- Mathematical symbol density  

---

## Design Principles

- Strict syllabus boundary enforcement  
- Separation of knowledge representation and exam filtering  
- No hallucinated analytics  
- Evidence-first insights  
- Modular and extensible architecture  
- Engineering realism over shortcuts  

---

## Technologies Used

- Python  
- SentenceTransformers  
- spaCy  
- scikit-learn  
- RapidFuzz  
- Tesseract OCR  
- Ollama (LLM-based extraction)  

---

## Running the Pipeline

1. Place syllabus PDF inside:  
   `data/raw/syllabus/`

2. Place question papers inside:  
   `data/raw/papers/`

3. Run:

```bash
python run_pipeline.py
```

Generated outputs include:

- topic_importance_<course>.json  
- grading_distribution_<course>.json  
- style_analysis_<course>.json  
- canonical_questions_<course>.json  

All outputs are evidence-backed and traceable to original questions.

---

## Engineering Challenges

This project required solving several non-trivial problems:

- Reliable question reconstruction from noisy OCR text  
- Preventing LLM hallucination during structured extraction  
- Enforcing strict syllabus alignment  
- Avoiding semantic coercion during exam-range filtering  
- Handling sub-question mark distribution correctly  
- Detecting canonical similarity across varied phrasings  
- Separating mapping logic from exam-specific analytics  

Each component was designed to prioritize correctness, robustness, and explainability.

---

## Scope

- Designed for VIT exam format (CAT-1, CAT-2, FAT)  
- Subject-level analytics  
- Institution-constrained implementation  
- Scalable to additional subjects  

---

## Future Improvements

- Interactive dashboard interface  
- Dependency-aware study sequencing  
- Visual analytics layer  
- Multi-subject expansion  
- Performance optimization for large datasets  

---

## Author

Mani Meghanath  
Software Engineering Project