import fitz  # PyMuPDF

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page_num, page in enumerate(doc):
        text += f"\n--- Page {page_num + 1} ---\n"
        text += page.get_text()
    doc.close()
    return text.strip()