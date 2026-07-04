"""
PDF text extraction with automatic OCR fallback.

Strategy per page:
  1. Extract text natively with PyMuPDF
  2. If fewer than MIN_CHARS characters extracted, the page is likely scanned
  3. Render the page to an image using PyMuPDF's built-in renderer (no poppler needed)
  4. Run Tesseract OCR on the rendered image
"""

import fitz          # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

# Tesseract path (Windows user-level install, no admin required)
def _find_tesseract():
    candidates = [
        r"C:\Users\blp046\tesseract\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",       # Linux / Docker
        "/usr/local/bin/tesseract",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return "tesseract"  # assume it is on PATH

pytesseract.pytesseract.tesseract_cmd = _find_tesseract()

# Pages with fewer characters than this are treated as scanned
MIN_CHARS = 50

# DPI for rendering scanned pages — 300 gives reliable OCR accuracy
RENDER_DPI = 300


def _render_page(page: fitz.Page) -> Image.Image:
    """Render a PDF page to a PIL Image using PyMuPDF — no poppler needed."""
    zoom = RENDER_DPI / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def _ocr_page(page: fitz.Page) -> str:
    """Run Tesseract OCR on a rendered PDF page."""
    img = _render_page(page)
    return pytesseract.image_to_string(
        img,
        lang="eng",
        config="--psm 3 --oem 3"
    ).strip()


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """
    Extract text from PDF bytes with automatic OCR fallback.

    Returns a dict:
        text              -- full extracted text across all pages
        pages_processed   -- total number of pages
        pages_ocr         -- number of pages processed via OCR
        character_count   -- total characters extracted
        extraction_method -- 'native', 'ocr', or 'mixed'
        page_methods      -- list of methods used per page
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_text = []
    pages_ocr = 0
    page_methods = []

    for i, page in enumerate(doc):
        label = f"\n--- Page {i + 1} ---\n"
        native = page.get_text().strip()

        if len(native.replace(" ", "").replace("\n", "")) >= MIN_CHARS:
            # Native extraction succeeded
            all_text.append(label + native)
            page_methods.append("native")
        else:
            # Scanned page — try OCR
            try:
                ocr_text = _ocr_page(page)
                if ocr_text:
                    all_text.append(label + ocr_text)
                    page_methods.append("ocr")
                else:
                    all_text.append(label + "[Page appears blank or unreadable]")
                    page_methods.append("ocr_empty")
                pages_ocr += 1
            except Exception as e:
                # OCR failed — include native text (even if sparse)
                all_text.append(label + native + f"\n[OCR failed: {str(e)[:80]}]")
                page_methods.append("ocr_failed")
                pages_ocr += 1

    doc.close()

    full_text = "\n".join(all_text).strip()

    if pages_ocr == 0:
        method = "native"
    elif pages_ocr == len(page_methods):
        method = "ocr"
    else:
        method = "mixed"

    return {
        "text": full_text,
        "pages_processed": len(page_methods),
        "pages_ocr": pages_ocr,
        "character_count": len(full_text),
        "extraction_method": method,
        "page_methods": page_methods,
    }