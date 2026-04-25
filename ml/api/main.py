"""
AuksionWatch FastAPI servisi.

Ishga tushirish:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    POST /analyze          — fayl yuklash (CSV yoki Excel)
    GET  /analyze/{job_id} — natijani olish
    GET  /health           — sog'liqni tekshirish
"""

import io
import sys
import uuid
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse

# scripts papkasi Python path'ga qo'shiladi
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.core_pipeline import run_pipeline

app = FastAPI(
    title="AuksionWatch API",
    description="E-auksion.uz ma'lumotlarida red-flag aniqlash",
    version="1.0.0",
)

JOBS_DIR = Path("data/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# Xotira ichida job holati
_jobs: dict[str, dict] = {}


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    CSV yoki Excel fayl yuklang → red-flag tahlil.

    Qabul qilinadi:
    - .xlsx / .xls  (e-auksion.uz export)
    - .csv          (UTF-8 yoki CP1251)

    Qaytaradi:
    - job_id: natijani olish uchun ID
    - stats:  qisqa statistika
    - top10:  eng shubhali 10 lot
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(400, "Faqat .xlsx, .xls yoki .csv fayl qabul qilinadi")

    content = await file.read()
    job_id  = str(uuid.uuid4())[:8]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_pipeline(
            input_path=io.BytesIO(content),
            filename=file.filename,
            output_dir=str(job_dir),
            verbose=False,
        )
    except Exception as e:
        raise HTTPException(500, f"Pipeline xatosi: {str(e)}")

    _jobs[job_id] = {
        "status": "done",
        "csv_path": result["output_csv"],
        "report_path": result["output_report"],
        "stats": result["stats"],
    }

    top10 = result["predictions"].head(10)[
        ["lot_number", "lot_url", "district", "start_price",
         "appraised_price", "price_ratio", "auction_count",
         "risk_score", "risk_level", "why_flagged"]
    ].to_dict(orient="records")

    return {
        "job_id":   job_id,
        "stats":    result["stats"],
        "top10":    top10,
        "csv_url":  f"/result/{job_id}/predictions.csv",
        "report_url": f"/result/{job_id}/report.txt",
    }


@app.get("/result/{job_id}/predictions.csv")
def get_csv(job_id: str):
    """To'liq predictions.csv ni yuklab olish."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job topilmadi")
    return FileResponse(
        job["csv_path"],
        media_type="text/csv",
        filename="predictions.csv",
    )


@app.get("/result/{job_id}/report.txt")
def get_report(job_id: str):
    """Matnli hisobotni yuklab olish."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job topilmadi")
    return FileResponse(
        job["report_path"],
        media_type="text/plain; charset=utf-8",
        filename="report.txt",
    )


@app.get("/result/{job_id}")
def get_result(job_id: str):
    """Job natijasi (stats + top10)."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job topilmadi")
    return {"job_id": job_id, "status": job["status"], "stats": job["stats"]}
