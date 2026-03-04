# PYQ Analyser
**Automsted Question Paper Parsing and Pattern Mining**

> PYQ Analyser converts previous year question papers into structured, syllabus-aligned insights that help students prepare smarter.

---

## Demo & Results Preview

*(Insert a GIF or screenshot of your generated analytics, charts, or web interface here to show the final output!)*

---

## Why This Project Was Built (The Problem)

Preparing for university exams is often inefficient. Students usually have two main resources:
1. Official syllabus
2. Previous Year Question Papers (PYQs)

Even though students have access to these, there is no structured way to analyze them together. As a result, students rely on guesswork, peer suggestions, or random topic prioritization, leading them to:
* Study the entire syllabus blindly.
* Miss frequently asked topics.
* Waste time on low-impact areas.
* Feel uncertainty before exams.

I wanted to build a transparent, explainable system (not a black-box AI) that answers:
* *Which topics appear most often in exams?*
* *Which modules carry the highest marks?*
* *Which questions repeat frequently?*
* *What is the style of the exam?*

---

##  What This System Does

The system analyzes multiple previous year papers and generates evidence-based exam insights:
* **Module-wise topic importance**
* **Frequently asked topics**
* **Repeated canonical questions**
* **Module-wise grading distribution**
* **Question style distribution** (numerical vs. descriptive)

*Note: The goal is not to predict questions, but to provide evidence-based preparation guidance.*

---

## Key Capabilities

### 1. Automatic Question Extraction
The system accepts PDF question papers (including scanned documents) and performs:
* OCR extraction
* Question reconstruction
* Mark inference
* Structured JSON generation

### 2. Syllabus-Constrained Topic Mapping
Each extracted question is strictly mapped to official syllabus topics using:
* Semantic embeddings (`all-MiniLM-L6-v2`)
* Concept overlap scoring
* Fuzzy matching
* Hierarchical module selection

**Current Mapping Accuracy:** ~90% accuracy (module level) | ~85% accuracy (topic level).

### 3. Evidence-Based Topic Importance
Topics are ranked based on frequency of occurrence and marks contribution. Each topic includes evidence references to actual exam questions.

**Importance Score Formula:**
```text
importance_score = (frequency_weight * normalized_frequency) + (marks_weight * normalized_marks)
```
*(Default weights: frequency_weight = 0.6, marks_weight = 0.4)*

### 4. Canonical Question Detection
Using embedding similarity and clustering, the system identifies questions that are repeatedly asked in different wording and tracks their occurrences across papers.

### 5. Question Style Analysis
Identifies exam style patterns by classifying questions into categories such as:
* Numerical
* Descriptive
* Analytical
* Diagrammatic

### 6. Module-Wise Grading Distribution
Computes how marks are distributed across modules historically to answer: *Which modules carry the most marks?*

---

## Challenges Faced During Development

* **OCR Noise:** Scanned PDFs produce messy text. Solved via OCR normalization, duplicate removal, question reconstruction logic, and sub-question handling.
* **Question Structure Recovery:** Exam papers have inconsistent formats. The system had to reconstruct question numbers, sub-questions, marks, and question boundaries.
* **Accurate Topic Mapping:** Simple keyword matching fails. Solved by combining semantic embeddings, concept overlap scoring, fuzzy token matching, and hierarchical module filtering.
* **Preventing Topic Hallucination:** A key design rule—the system must never invent new topics. All mappings are constrained strictly to the syllabus.

---

## System Architecture

The system follows a pipeline-based architecture:

```text
Syllabus PDF ─────────┐
                      ▼
             Syllabus Extraction
                      │
                      ▼
Question Paper OCR ───┤
                      ▼
            Question Reconstruction
                      │
                      ▼
         JSON Cleaning & Normalization
                      │
                      ▼
             Topic Mapping Engine
                      │
                      ▼
             Analytics Generation
```

### Project Structure
```text
project/
├── backend/
│   ├── main.py
│   ├── pipeline_runner.py
│   └── job_manager.py
├── frontend/
│   └── templates/
│       └── index.html
├── analytics/
│   ├── canonical_engine.py
│   ├── config.py
│   ├── data_loader.py
│   ├── embedding_engine.py
│   ├── grading_engine.py
│   ├── importance_engine.py
│   ├── module_filter.py
│   ├── run_analytics.py
│   ├── style_engine.py
│   ├── subject_gate.py
│   ├── syllabus_enrichment.py
│   ├── text_utils.py
│   └── topic_mapper.py
└── modules/
    ├── course_check.py
    ├── json_cleaning.py
    ├── question_extractor.py
    ├── syllabus_extract.py
    └── text_extract.py
```

---

## Installation & Usage

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/pyq-analyser.git](https://github.com/yourusername/pyq-analyser.git)
cd pyq-analyser
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Running the System
Start the FastAPI server:
```bash
python backend/main.py
```
Open the interface in your browser. 

**The Workflow:**
1. Upload syllabus PDF.
2. Upload at least 3 previous year papers.
3. Select module range.
4. Run analysis.

---

## Example Output Insights

The system generates analytics outputs (backed with exact question references) that answer:
* Which topics appear most frequently in Module 3?
* Which questions repeat across multiple years?
* What percentage of the exam is numerical?
* Which modules carry the highest marks historically?

---

## Future Directions

This project currently focuses on VIT-style syllabus structures, but the long-term goal is to evolve it into a broader, reusable academic analytics platform. Future plans include:
* Converting the system into a full web application.
* Supporting multiple universities and syllabus formats.
* Allowing automatic PYQ dataset ingestion.

---

## Project Status

**Current implementation includes:**
* Full analytics pipeline
* Topic mapping engine
* Canonical question detection
* FastAPI backend
* Web interface

*Further improvements will focus on scalability, UI enhancements, and multi-institution support.*
