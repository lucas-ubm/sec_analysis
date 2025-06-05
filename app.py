from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os
import uuid
from pathlib import Path
import asyncio
from typing import List
import extract_mentions
import pandas as pd

app = FastAPI(title="SEC Filing Analysis Tool")

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("datasets", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Store running jobs
running_jobs = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze(
    keywords: str = Form(...),
    start_year: int = Form(...),
    end_year: int = Form(...),
    filing_types: str = Form(...),
    user_agent: str = Form(...),
    cik_tickers: str = Form(...),
    ignore_missing: str = Form(None)
):
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Parse inputs
    keywords_list = [k.strip() for k in keywords.split(",")]
    filing_types_list = [ft.strip() for ft in filing_types.split(",")]
    cik_tickers_list = [ct.strip() for ct in cik_tickers.split(",")]
    ignore_missing_flag = ignore_missing == "yes"
    
    # Create config
    config = {
        "topic": f"analysis_{job_id}",
        "filing_types": filing_types_list,
        "ignore_missing_filings": ignore_missing_flag,
        "edgar_crawler": {
            "start_year": start_year,
            "end_year": end_year,
            "quarters": [1, 2, 3, 4],
            "filing_types": filing_types_list,
            "cik_tickers": cik_tickers_list,
            "user_agent": user_agent,
            "skip_present_indices": True
        },
        "extract_items": {
            "items_to_extract": [],
            "remove_tables": True,
            "skip_extracted_filings": True
        },
        "extract_keywords": {
            "search_terms": keywords_list,
            "ignore_case": True,
            "regex_search": True,
            "mentions_name": f"analysis_{job_id}_mentions"
        }
    }
    
    # Save config
    config_path = f"datasets/config_{job_id}.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    
    # Start analysis in background
    running_jobs[job_id] = {
        "status": "running",
        "config": config,
        "config_path": config_path
    }
    
    # Run analysis in background
    asyncio.create_task(run_analysis(job_id))
    
    return {"job_id": job_id}

async def run_analysis(job_id: str):
    try:
        config_path = running_jobs[job_id]["config_path"]
        extract_mentions.main(config_path)
        running_jobs[job_id]["status"] = "completed"
    except Exception as e:
        running_jobs[job_id]["status"] = "failed"
        running_jobs[job_id]["error"] = str(e)

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in running_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return running_jobs[job_id]

@app.get("/download/{job_id}")
async def download_results(job_id: str):
    if job_id not in running_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = running_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    mentions_name = job["config"]["extract_keywords"]["mentions_name"]
    excel_path = f"datasets/{mentions_name}.xlsx"
    
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Results file not found")
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"sec_analysis_{job_id}.xlsx"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 