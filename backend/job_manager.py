import uuid
from threading import Thread

jobs = {}

def create_job():
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "logs": [],
        "result": None
    }
    return job_id

def log(job_id, message):
    jobs[job_id]["logs"].append(message)

def complete_job(job_id, result):
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["result"] = result

def fail_job(job_id, error):
    jobs[job_id]["status"] = "error"
    jobs[job_id]["logs"].append(str(error))

def get_job(job_id):
    return jobs.get(job_id)