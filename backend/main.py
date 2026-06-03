from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdf_parser import extract_text_from_pdf
from extractor import extract_information
import uvicorn

app = FastAPI(
    title="PDF Information Extractor API",
    description="Extracts structured information from PDF documents using a local LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": "llama3.2", "deployment": "local"}

@app.post("/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and receive structured JSON extraction.
    All processing happens locally - no data leaves the machine.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted. The PDF may be image-based or scanned."
            )

        result = extract_information(text)

        return {
            "success": True,
            "filename": file.filename,
            "pages_processed": text.count("--- Page"),
            "character_count": len(text),
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)