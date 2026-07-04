import json
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdf_parser import extract_text_from_pdf
from extractor import extract_information
import uvicorn
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

app = FastAPI(
    title="PDF Information Extractor API",
    description=(
        "Extracts structured information from PDF documents using a local LLM. "
        "Supports single and batch document processing. "
        "Automatically detects scanned PDFs and applies OCR where needed. "
        "No data leaves the machine."
    ),
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model": "llama3.2",
        "deployment": "local",
        "ocr_support": True,
        "batch_support": True,
        "version": "3.0.0"
    }


def process_single_file(file_bytes: bytes, filename: str) -> dict:
    """
    Core extraction logic shared by single and batch endpoints.
    Returns a result dict. Raises HTTPException on hard failures.
    """
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"{filename}: only PDF files are supported")

    doc = extract_text_from_pdf(file_bytes)

    if not doc["text"].strip():
        raise HTTPException(status_code=400, detail=f"{filename}: no text could be extracted")

    result = extract_information(doc["text"])

    return {
        "success": True,
        "filename": filename,
        "pages_processed": doc["pages_processed"],
        "pages_ocr": doc["pages_ocr"],
        "character_count": doc["character_count"],
        "extraction_method": doc["extraction_method"],
        "page_methods": doc["page_methods"],
        "extraction": result
    }


@app.post("/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """
    Upload a single PDF and receive structured JSON extraction.
    Scanned PDFs handled automatically via OCR.
    All processing local: no data leaves the machine.
    """
    try:
        file_bytes = await file.read()
        return process_single_file(file_bytes, file.filename)
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned malformed JSON. Try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract-batch")
async def extract_batch(files: List[UploadFile] = File(...)):
    """
    Upload multiple PDFs and receive structured JSON extraction for each.
    Files are processed sequentially. One failed file does not stop the batch.
    Returns results in the same order as uploaded files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per batch")

    results = []
    successful = 0
    failed = 0

    for file in files:
        try:
            file_bytes = await file.read()
            result = process_single_file(file_bytes, file.filename)
            results.append(result)
            successful += 1
        except HTTPException as e:
            # Per-file error: log it and continue with remaining files
            results.append({
                "success": False,
                "filename": file.filename,
                "error": e.detail
            })
            failed += 1
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
            failed += 1

    return {
        "batch_complete": True,
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "results": results
    }


@app.post("/extract-text")
async def extract_text_only(file: UploadFile = File(...)):
    """Return raw extracted text without LLM processing. Useful for debugging OCR output."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    doc = extract_text_from_pdf(file_bytes)

    return {
        "filename": file.filename,
        "text": doc["text"],
        "pages_processed": doc["pages_processed"],
        "pages_ocr": doc["pages_ocr"],
        "character_count": doc["character_count"],
        "extraction_method": doc["extraction_method"],
        "page_methods": doc["page_methods"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)