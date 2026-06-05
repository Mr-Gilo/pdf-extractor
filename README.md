# PDF Information Extractor

A locally hosted AI tool that extracts structured information from PDF documents.
All processing happens on your machine — no data leaves your device.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)

## Architecture

PDF Upload → PyMuPDF (text extraction) → FastAPI → Ollama (llama3.2) → Structured JSON

↑

Streamlit UI

## Features

- Local LLM inference via Ollama - no API keys, no cloud dependency
- PDF text extraction via PyMuPDF
- Structured JSON output via custom prompt engineering
- REST API via FastAPI with Swagger documentation at /docs
- Streamlit frontend with PDF upload, results display, and JSON download
- Extracts: document type, parties, dates, monetary amounts, key facts, summary

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Ollama (llama3.2) |
| Backend | FastAPI + Uvicorn |
| PDF Parsing | PyMuPDF (fitz) |
| Frontend | Streamlit |
| Data Validation | Pydantic |

## Prerequisites

- Python 3.11+
- Ollama installed: https://ollama.com/download
- llama3.2 model: `ollama pull llama3.2`

## Installation

```bash
# Clone the repository
git clone https://github.com/Mr-Gilo/pdf-extractor.git
cd pdf-extractor

# Create and activate environment
conda create -n pdf-extractor python=3.11 -y
conda activate pdf-extractor

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
pip install -r requirements.txt
```

## Running the Application

**Terminal 1 - Start Ollama:**
```bash
ollama serve
```

**Terminal 2 - Start the backend:**
```bash
conda activate pdf-extractor
cd backend
python main.py
```
Backend runs at http://localhost:8000
API documentation at http://localhost:8000/docs

**Terminal 3 - Start the frontend:**
```bash
conda activate pdf-extractor
streamlit run app.py
```
Frontend runs at http://localhost:8501

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Check API and model status |
| POST | /extract | Upload PDF and extract structured JSON |

## Example Output

```json
{
  "document_type": "Motor Insurance Claim",
  "parties": [
    {"text": "Babangida Abdullahi", "context": "Claimant"},
    {"text": "GILO Insurance Ltd", "context": "Defendant"}
  ],
  "dates": [
    {"text": "15 March 2026", "context": "Date of incident"},
    {"text": "22 April 2026", "context": "Date of claim submission"}
  ],
  "monetary_amounts": [
    {"text": "£12,500", "context": "Claimed damages"}
  ],
  "key_facts": [
    "Rear-end collision on M6 motorway",
    "Third party admitted liability",
    "Vehicle declared total loss"
  ],
  "summary": "Motor insurance claim following a rear-end collision..."
}
```

## Roadmap

- [x] PDF text extraction
- [x] Local LLM integration via Ollama
- [x] FastAPI REST backend
- [x] Streamlit frontend
- [x] Docker containerisation

## Use Case

This tool is designed to be domain-agnostic and can extract structured information from any text-based PDF for document analysis