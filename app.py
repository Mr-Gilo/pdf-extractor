import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="PDF Information Extractor",
    page_icon="📄",
    layout="wide"
)

# Header
st.title("📄 PDF Information Extractor")
st.markdown(
    "Upload a PDF document to extract structured information "
    "using a **locally hosted AI model**. "
    "Scanned and image-based PDFs are handled automatically via OCR. "
    "No data leaves your machine."
)

# Sidebar
with st.sidebar:
    st.header("System Status")
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            info = r.json()
            st.success("API Online")
            st.markdown(f"**Model:** {info['model']}")
            st.markdown(f"**Deployment:** {info['deployment']}")
            st.markdown(
                f"**OCR Support:** {'✅ Enabled' if info.get('ocr_support') else '❌ Disabled'}"
            )
            st.markdown(f"**Version:** {info.get('version', '1.0.0')}")
        else:
            st.error("API Error")
    except Exception:
        st.error("API Offline")
        st.markdown("Start the backend with:\n```\npython backend/main.py\n```")

    st.divider()
    st.header("About")
    st.markdown("""
This tool demonstrates:
- Local LLM inference via **Ollama (llama3.2)**
- Native PDF text extraction via **PyMuPDF**
- Automatic OCR fallback via **Tesseract** for scanned PDFs
- REST API via **FastAPI**
- Structured JSON output via **prompt engineering**

Both text-based and scanned PDFs are supported.
    """)

    st.divider()
    st.header("Extraction Methods")
    st.markdown("""
| Method | When used |
|--------|-----------|
| 🟢 Native | Text-based PDF - fast, accurate |
| 🟡 OCR | Scanned page - Tesseract at 300 DPI |
| 🔵 Mixed | Some pages native, some OCR |
    """)

# File upload
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type="pdf",
    help="Upload any PDF - text-based or scanned. OCR is applied automatically."
)

if uploaded_file is not None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Filename", uploaded_file.name)
    col2.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
    col3.metric("Type", "PDF")

    st.divider()

    if st.button("Extract Information", type="primary", use_container_width=True):
        with st.spinner("Processing document with local AI model..."):
            try:
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf"
                    )
                }
                response = requests.post(
                    f"{API_URL}/extract",
                    files=files,
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()
                    extraction = data["extraction"]
                    method = data.get("extraction_method", "native")
                    pages_ocr = data.get("pages_ocr", 0)
                    pages_total = data.get("pages_processed", 1)

                    # Success banner with OCR info
                    if method == "native":
                        st.success(
                            f"✅ Extraction complete - "
                            f"{data['character_count']:,} characters across "
                            f"{pages_total} page(s) · Native text extraction"
                        )
                    elif method == "ocr":
                        st.success(
                            f"✅ Extraction complete - "
                            f"{data['character_count']:,} characters across "
                            f"{pages_total} page(s) · OCR applied (scanned PDF)"
                        )
                    else:
                        st.success(
                            f"✅ Extraction complete - "
                            f"{data['character_count']:,} characters across "
                            f"{pages_total} page(s) · Mixed ({pages_ocr} page(s) via OCR)"
                        )

                    # OCR status badge
                    method_labels = {
                        "native": ("🟢", "Native Text", "All pages extracted directly from PDF text layer."),
                        "ocr":    ("🟡", "OCR (Scanned PDF)", f"All {pages_total} page(s) processed via Tesseract OCR at 300 DPI."),
                        "mixed":  ("🔵", "Mixed Extraction", f"{pages_ocr} of {pages_total} page(s) required OCR. Remaining pages used native extraction."),
                    }
                    icon, label, desc = method_labels.get(method, ("⚪", "Unknown", ""))
                    st.info(f"{icon} **Extraction Method: {label}** - {desc}")

                    # Document overview
                    st.subheader("Document Overview")
                    ov1, ov2 = st.columns(2)
                    with ov1:
                        st.markdown("**Document Type**")
                        st.info(extraction.get("document_type", "Unknown"))
                    with ov2:
                        st.markdown("**Summary**")
                        st.info(extraction.get("summary", "No summary available"))

                    st.divider()

                    # Parties
                    st.subheader("Parties Identified")
                    parties = extraction.get("parties", [])
                    if parties:
                        for p in parties:
                            st.markdown(
                                f"- **{p['text']}** "
                                f"{'- ' + p['context'] if p.get('context') else ''}"
                            )
                    else:
                        st.markdown("_No parties identified_")

                    st.divider()

                    # Dates and Amounts side by side
                    col_d, col_m = st.columns(2)

                    with col_d:
                        st.subheader("Dates")
                        dates = extraction.get("dates", [])
                        if dates:
                            for d in dates:
                                st.markdown(
                                    f"- **{d['text']}** "
                                    f"{'- ' + d['context'] if d.get('context') else ''}"
                                )
                        else:
                            st.markdown("_No dates identified_")

                    with col_m:
                        st.subheader("Monetary Amounts")
                        amounts = extraction.get("monetary_amounts", [])
                        if amounts:
                            for a in amounts:
                                st.markdown(
                                    f"- **{a['text']}** "
                                    f"{'- ' + a['context'] if a.get('context') else ''}"
                                )
                        else:
                            st.markdown("_No monetary amounts identified_")

                    st.divider()

                    # Key facts
                    st.subheader("Key Facts")
                    facts = extraction.get("key_facts", [])
                    if facts:
                        for fact in facts:
                            st.markdown(f"- {fact}")
                    else:
                        st.markdown("_No key facts identified_")

                    st.divider()

                    # Per-page extraction methods (shown only when OCR was used)
                    if pages_ocr > 0:
                        page_methods = data.get("page_methods", [])
                        with st.expander(
                            f"📋 Per-page extraction methods "
                            f"({pages_ocr} page(s) used OCR)"
                        ):
                            method_icons = {
                                "native": "🟢 Native",
                                "ocr": "🟡 OCR",
                                "ocr_empty": "⚠️ OCR (blank)",
                                "ocr_failed": "❌ OCR failed"
                            }
                            for i, m in enumerate(page_methods, 1):
                                label = method_icons.get(m, m)
                                st.markdown(f"Page {i}: {label}")

                    # Raw JSON and download
                    with st.expander("View Raw JSON Output"):
                        st.json(extraction)

                    st.download_button(
                        label="Download Extracted JSON",
                        data=json.dumps(extraction, indent=2),
                        file_name=f"{uploaded_file.name.replace('.pdf', '')}_extracted.json",
                        mime="application/json",
                        use_container_width=True
                    )

                else:
                    st.error(
                        f"Error {response.status_code}: "
                        f"{response.json().get('detail', 'Unknown error')}"
                    )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend API. "
                    "Make sure it is running in a separate terminal."
                )
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")