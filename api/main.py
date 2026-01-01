from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os
from pathlib import Path
import tempfile
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EXCEL_PARAM_FILE
from src.llm import LLMEngine
from src.extractors import BureauExtractor, GstExtractor

app = FastAPI(
    title="Document Intelligence API",
    description="Extract data from Bureau Reports and GST Returns",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_engine = None
bureau_extractor = None
gst_extractor = None

def get_extractors():
    global llm_engine, bureau_extractor, gst_extractor

    if llm_engine is None:
        llm_engine = LLMEngine()
        bureau_extractor = BureauExtractor(str(EXCEL_PARAM_FILE), llm_engine)
        gst_extractor = GstExtractor(llm_engine)

    return bureau_extractor, gst_extractor


class ExtractionResponse(BaseModel):
    bureau_parameters: Optional[Dict[str, Any]] = None
    gst_sales: Optional[List[Dict[str, Any]]] = None
    overall_confidence_score: float = 0.0
    status: str = "success"
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str
    ollama_status: str


@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "name": "Document Intelligence API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "extract_bureau": "/api/extract/bureau",
            "extract_gst": "/api/extract/gst",
            "extract_auto": "/api/extract/auto"
        }
    }


@app.post("/api/extract/bureau", response_model=ExtractionResponse)
async def extract_bureau(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        bureau_ext, _ = get_extractors()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            extracted_data = bureau_ext.extract(tmp_file_path)

            bureau_params = {
                k: v.model_dump() for k, v in extracted_data.items()
            }

            confidences = [v.confidence for v in extracted_data.values() if v.confidence > 0]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return ExtractionResponse(
                bureau_parameters=bureau_params,
                overall_confidence_score=round(overall_confidence, 2),
                status="success"
            )
        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/api/extract/gst", response_model=ExtractionResponse)
async def extract_gst(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        _, gst_ext = get_extractors()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            extracted_data = gst_ext.extract(tmp_file_path)
            gst_sales = [item.model_dump() for item in extracted_data]
            confidences = [item.confidence for item in extracted_data if item.confidence > 0]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return ExtractionResponse(
                gst_sales=gst_sales,
                overall_confidence_score=round(overall_confidence, 2),
                status="success"
            )
        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/api/extract/auto", response_model=ExtractionResponse)
async def extract_auto(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    filename = file.filename.lower()

    if "gst" in filename or "3b" in filename:
        return await extract_gst(file)
    elif "bureau" in filename or "crif" in filename or "report" in filename:
        return await extract_bureau(file)
    else:
        raise HTTPException(
            status_code=400,
            detail="Could not auto-detect document type. Please use specific endpoints."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
