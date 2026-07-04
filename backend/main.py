import json
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
        "Automatically detects scanned PDFs and applies OCR where needed. "
        "No data leaves the machine."
    ),
    version="2.0.0"
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
        "version": "2.0.0"
    }


@app.post("/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and receive structured JSON extraction.
    Scanned and image-based PDFs are handled automatically via OCR.
    All processing happens locally - no data leaves the machine.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        file_bytes = await file.read()

        # Extract text with OCR fallback
        doc = extract_text_from_pdf(file_bytes)

        if not doc["text"].strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from this PDF."
            )

        # Run LLM extraction on the text
        result = extract_information(doc["text"])

        return {
            "success": True,
            "filename": file.filename,
            "pages_processed": doc["pages_processed"],
            "pages_ocr": doc["pages_ocr"],
            "character_count": doc["character_count"],
            "extraction_method": doc["extraction_method"],
            "page_methods": doc["page_methods"],
            "extraction": result
        }

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM returned malformed JSON. Try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


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