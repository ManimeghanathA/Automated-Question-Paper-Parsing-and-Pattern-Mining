from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path
from threading import Thread
import json
import os

# Existing modules
from modules.syllabus_extract import parse_syllabus_pdf
from modules.text_extract import run_ocr
from modules.course_check import validate_papers
from modules.question_extractor import run_question_extraction
from modules.json_cleaning import clean_all_papers

from analytics.data_loader import load_questions
from analytics.topic_mapper import map_questions_to_topics
from analytics.importance_engine import compute_topic_importance
from analytics.grading_engine import compute_grading_distribution
from analytics.style_engine import compute_style_distribution
from analytics.canonical_engine import compute_canonical_questions
from analytics.syllabus_enrichment import get_or_create_enriched_syllabus

# Job system
from backend.job_manager import create_job, log, complete_job, fail_job, get_job

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
SYLLABUS_OUTPUT_DIR = BASE_DIR / "data" / "extracted" / "syllabus"
ENRICHED_DIR = BASE_DIR / "data" / "extracted" / "enriched_syllabus"
OCR_OUTPUT_DIR = BASE_DIR / "data" / "extracted" / "ocr_text"
STRUCTURED_OUTPUT_DIR = BASE_DIR / "data" / "extracted" / "structured_json"
CLEANED_OUTPUT_DIR = BASE_DIR / "data" / "extracted" / "cleaned_json"
ANALYTICS_OUTPUT_DIR = BASE_DIR / "data" / "analytics"
COURSE_MAPPING_PATH = BASE_DIR / "data" / "source" / "course_mapping.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_SYLLABUS_PATH = None
CURRENT_COURSE_CODE = None

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ----------------------------
# Upload Syllabus
# ----------------------------
@app.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    global CURRENT_SYLLABUS_PATH, CURRENT_COURSE_CODE

    try:
        syllabus_path = UPLOAD_DIR / file.filename

        contents = await file.read()
        size_mb = len(contents) / (1024 * 1024)

        if size_mb > 15:
            return JSONResponse({
                "success": False,
                "stage": "UPLOAD",
                "error": "Syllabus file too large. Please upload official VIT PDF."
            }, status_code=400)

        with open(syllabus_path, "wb") as f:
            f.write(contents)

        # Parse syllabus
        output_json_path = parse_syllabus_pdf(
            syllabus_path,
            SYLLABUS_OUTPUT_DIR
        )

    except Exception as e:
        return JSONResponse({
            "success": False,
            "stage": "PARSING",
            "error": f"{file.filename} could not be parsed as a valid VIT syllabus. {str(e)}"
        }, status_code=400)

    # Now validate JSON structure
    try:
        with open(output_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Structural validation
        required_keys = ["course_code", "course_title", "modules"]

        for key in required_keys:
            if key not in data:
                raise Exception(f"Missing key: {key}")

        if not isinstance(data["modules"], list) or len(data["modules"]) == 0:
            raise Exception("No valid modules detected.")

        CURRENT_SYLLABUS_PATH = output_json_path
        CURRENT_COURSE_CODE = data["course_code"]

        return {
            "success": True,
            "course_code": data["course_code"],
            "course_title": data["course_title"],
            "modules": [
                m["module_id"]
                for m in data["modules"]
                if m.get("topics")
            ]
        }

    except Exception as e:
        return JSONResponse({
            "success": False,
            "stage": "VALIDATION",
            "error": f"Syllabus structure invalid. {str(e)}"
        }, status_code=400)

# ----------------------------
# Upload Papers + Validate
# ----------------------------
@app.post("/upload-papers")
async def upload_papers(files: list[UploadFile] = File(...)):
    global CURRENT_SYLLABUS_PATH

    if not CURRENT_SYLLABUS_PATH:
        return JSONResponse({
            "success": False,
            "stage": "SYLLABUS",
            "error": "Upload syllabus first."
        }, status_code=400)

    if len(files) < 3:
        return JSONResponse({
            "success": False,
            "stage": "VALIDATION",
            "error": "Minimum 3 PDFs required."
        }, status_code=400)

    for file in files:
        try:
            contents = await file.read()
            size_mb = len(contents) / (1024 * 1024)

            if size_mb > 25:
                return JSONResponse({
                    "success": False,
                    "stage": "UPLOAD",
                    "error": f"{file.filename} exceeds 25MB limit. Rescan at 300 DPI."
                }, status_code=400)

            path = UPLOAD_DIR / file.filename
            with open(path, "wb") as f:
                f.write(contents)

            # OCR
            run_ocr(
                str(path),
                str(OCR_OUTPUT_DIR / f"{path.stem}.txt")
            )

        except Exception as e:
            return JSONResponse({
                "success": False,
                "stage": "OCR",
                "error": f"{file.filename} could not be processed. {str(e)}"
            }, status_code=400)

    # SUBJECT VALIDATION
    try:
        valid, invalid = validate_papers(
            OCR_OUTPUT_DIR,
            CURRENT_SYLLABUS_PATH,
            COURSE_MAPPING_PATH
        )

        if invalid:
            return {
                "success": False,
                "stage": "SUBJECT_GATE",
                "error": "One or more papers do not match the syllabus course code.",
                "invalid": invalid,
                "syllabus_code": CURRENT_COURSE_CODE
            }

        return {
            "success": True,
            "valid": True
        }

    except Exception as e:
        return JSONResponse({
            "success": False,
            "stage": "VALIDATION",
            "error": f"Subject validation failed: {str(e)}"
        }, status_code=400)


# ----------------------------
# Run Full Analysis
# ----------------------------
@app.post("/run-analysis")
async def run_analysis(start_module: int, end_module: int):

    job_id = create_job()

    def background():
        try:
            log(job_id, "Loading syllabus...")
            enriched_path = get_or_create_enriched_syllabus(CURRENT_SYLLABUS_PATH, ENRICHED_DIR)

            with open(enriched_path, "r", encoding="utf-8") as f:
                enriched_data = json.load(f)

            selected_modules = [
                m for m in enriched_data["modules"]
                if start_module <= m["module_id"] <= end_module
            ]

            log(job_id, "Extracting structured questions...")
            for txt in OCR_OUTPUT_DIR.glob("*.txt"):
                run_question_extraction(txt, STRUCTURED_OUTPUT_DIR)

            log(job_id, "Cleaning JSON...")
            clean_all_papers(STRUCTURED_OUTPUT_DIR, CLEANED_OUTPUT_DIR, CURRENT_SYLLABUS_PATH)

            log(job_id, "Mapping topics...")
            questions = load_questions(CLEANED_OUTPUT_DIR)
            mapped = map_questions_to_topics(questions, selected_modules, CURRENT_COURSE_CODE)

            log(job_id, "Computing importance...")
            importance = compute_topic_importance(mapped, CURRENT_COURSE_CODE, ANALYTICS_OUTPUT_DIR)

            log(job_id, "Computing grading...")
            grading = compute_grading_distribution(mapped, CURRENT_COURSE_CODE, ANALYTICS_OUTPUT_DIR)

            log(job_id, "Computing style...")
            style = compute_style_distribution(mapped, CURRENT_COURSE_CODE, ANALYTICS_OUTPUT_DIR)

            log(job_id, "Computing canonical clusters...")
            canonical = compute_canonical_questions(mapped, CURRENT_COURSE_CODE, ANALYTICS_OUTPUT_DIR)

            complete_job(job_id, {
                "importance": importance,
                "grading": grading,
                "style": style,
                "canonical": canonical
            })

        except Exception as e:
            fail_job(job_id, str(e))

    Thread(target=background).start()

    return {"job_id": job_id}


@app.get("/job-status/{job_id}")
async def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return JSONResponse({"error": "Invalid job id"}, status_code=404)
    return job


# ----------------------------
# Cleanup Intermediate Files
# ----------------------------
@app.post("/cleanup")
async def cleanup():
    """
    Deletes all intermediate files generated during a run so the next
    run starts from a clean state.  Deliberately skips enriched_syllabus
    (expensive LLM call) and data/source (static mapping files).
    """
    import shutil

    dirs_to_clear = [
        UPLOAD_DIR,
        SYLLABUS_OUTPUT_DIR,
        OCR_OUTPUT_DIR,
        STRUCTURED_OUTPUT_DIR,
        CLEANED_OUTPUT_DIR,
        ANALYTICS_OUTPUT_DIR,
    ]

    cleared = []
    for d in dirs_to_clear:
        if d.exists():
            shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)
            cleared.append(str(d.name))

    # Also reset in-memory state
    global CURRENT_SYLLABUS_PATH, CURRENT_COURSE_CODE
    CURRENT_SYLLABUS_PATH = None
    CURRENT_COURSE_CODE = None

    return {"cleared": cleared}