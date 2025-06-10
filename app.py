from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
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
    config_file: UploadFile = File(None),
    keywords: str = Form(None),
    start_year: int = Form(None),
    end_year: int = Form(None),
    filing_types: str = Form(None),
    user_agent: str = Form(...),
    cik_tickers: str = Form(None),
    ignore_missing: str = Form(None)
):
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # If config file is provided, use it as base
    if config_file and config_file.filename:  # Check if a file was actually uploaded
        try:
            config_content = await config_file.read()
            config = json.loads(config_content)
            
            # Handle simplified config format
            if "topic" in config:
                # This is a simplified config, convert to complete format
                complete_config = {
                    "edgar_crawler": {
                        "start_year": config["edgar_crawler"]["start_year"],
                        "end_year": config["edgar_crawler"]["end_year"],
                        "quarters": config["edgar_crawler"]["quarters"],
                        "filing_types": config["filing_types"],
                        "cik_tickers": config["edgar_crawler"]["cik_tickers"],
                        "user_agent": user_agent,
                        "raw_filings_folder": "raw_filings",
                        "indices_folder": "indices",
                        "filings_metadata_file": "filings_metadata.csv",
                        "skip_present_indices": config["edgar_crawler"]["skip_present_indices"]
                    },
                    "extract_items": {
                        "raw_filings_folder": "raw_filings",
                        "extracted_filings_folder": "extracted_filings",
                        "filings_metadata_file": "filings_metadata.csv",
                        "filing_types": config["filing_types"],
                        "items_to_extract": config["extract_items"]["items_to_extract"],
                        "remove_tables": config["extract_items"]["remove_tables"],
                        "skip_extracted_filings": config["extract_items"]["skip_extracted_filings"]
                    },
                    "extract_keywords": {
                        "search_terms": config["extract_keywords"]["search_terms"],
                        "ignore_case": config["extract_keywords"]["ignore_case"],
                        "regex_search": config["extract_keywords"]["regex_search"],
                        "mentions_name": f"analysis_{job_id}_mentions",
                        "exclude_columns": config["extract_keywords"].get("exclude_columns", [])
                    }
                }
                config = complete_config
            else:
                # This is a complete config, just ensure mentions_name is set
                if "extract_keywords" not in config:
                    config["extract_keywords"] = {}
                if "mentions_name" not in config["extract_keywords"]:
                    config["extract_keywords"]["mentions_name"] = f"analysis_{job_id}_mentions"
            
            # Update user agent in config
            config["edgar_crawler"]["user_agent"] = user_agent
            
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON config file")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading config file: {str(e)}")
    else:
        # Parse inputs for manual config
        if not all([keywords, start_year, end_year, filing_types]):
            raise HTTPException(status_code=400, detail="Missing required fields for manual config")
            
        keywords_list = [k.strip() for k in keywords.split(",")]
        filing_types_list = [ft.strip() for ft in filing_types.split(",")]
        cik_tickers_list = [ct.strip() for ct in cik_tickers.split(",")]
        ignore_missing_flag = ignore_missing == "yes"
        
        # Create complete config
        config = {
            "edgar_crawler": {
                "start_year": start_year,
                "end_year": end_year,
                "quarters": [1, 2, 3, 4],
                "filing_types": filing_types_list,
                "cik_tickers": cik_tickers_list,
                "user_agent": user_agent,
                "raw_filings_folder": "raw_filings",
                "indices_folder": "indices",
                "filings_metadata_file": "filings_metadata.csv",
                "skip_present_indices": True
            },
            "extract_items": {
                "raw_filings_folder": "raw_filings",
                "extracted_filings_folder": "extracted_filings",
                "filings_metadata_file": "filings_metadata.csv",
                "filing_types": filing_types_list,
                "items_to_extract": [],
                "remove_tables": True,
                "skip_extracted_filings": True
            },
            "extract_keywords": {
                "search_terms": keywords_list,
                "ignore_case": True,
                "regex_search": True,
                "mentions_name": f"analysis_{job_id}_mentions",
                "exclude_columns": []
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