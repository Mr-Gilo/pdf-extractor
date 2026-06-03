# PDF Information Extractor

A local AI-powered tool that extracts structured information from PDF documents.
Built as a demonstration of LLM integration, document processing, and API design.

## Architecture

- **Backend:** FastAPI (Python) with PyMuPDF for PDF parsing
- **LLM:** Ollama (llama3.2) — fully local, no cloud dependency
- **Frontend:** Streamlit
- **Output:** Structured JSON with parties, dates, amounts, key facts, and summary

## Setup

### Prerequisites
- Python 3.11+
- Ollama installed and running: https://ollama.com
- llama3.2 model pulled: `ollama pull llama3.2`

### Install dependencies
```bash
conda create -n pdf-extractor python=3.11 -y
conda activate pdf-extractor
pip install fastapi uvicorn python-multipart pymupdf ollama pydantic python-dotenv streamlit requests
```

### Run

**Terminal 1 — Start the backend:**
```bash
conda activate pdf-extractor
cd backend
python main.py
```

**Terminal 2 — Start the frontend:**
```bash
conda activate pdf-extractor
cd C:\Users\blp046\pdf-extractor
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## API Documentation

With the backend running, visit http://localhost:8000/docs for the interactive
Swagger UI showing all available endpoints.

## Use Case

Designed for motor insurance and legal document analysis. Extracts:
- Parties involved (claimants, defendants, solicitors)
- Key dates (incident, hearing, filing)
- Monetary amounts (claims, settlements, costs)
- Key facts and document summary