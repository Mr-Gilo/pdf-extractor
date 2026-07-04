import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="PDF Information Extractor",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF Information Extractor")
st.markdown(
    "Upload PDF documents to extract structured information using a "
    "**locally hosted AI model**. "
    "Scanned PDFs are handled automatically via OCR. "
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
                f"**OCR Support:** {'Yes' if info.get('ocr_support') else 'No'}"
            )
            st.markdown(
                f"**Batch Support:** {'Yes' if info.get('batch_support') else 'No'}"
            )
            st.markdown(f"**Version:** {info.get('version', '1.0.0')}")
        else:
            st.error("API Error")
    except Exception:
        st.error("API Offline")
        st.markdown("Start the backend:\n```\npython backend/main.py\n```")

    st.divider()
    st.header("About")
    st.markdown("""
This tool demonstrates:
- Local LLM inference via **Ollama (llama3.2)**
- PDF text extraction via **PyMuPDF**
- Automatic OCR fallback via **Tesseract**
- Single and **batch document processing**
- REST API via **FastAPI**

Both text-based and scanned PDFs are supported.
    """)

    st.divider()
    st.header("Extraction Methods")
    st.markdown("""
| Method | When used |
|--------|-----------|
| Native | Text-based PDF |
| OCR | Scanned page |
| Mixed | Some pages each |
    """)


def display_extraction_result(data: dict):
    """Render a single extraction result."""
    extraction = data["extraction"]
    method = data.get("extraction_method", "native")
    pages_ocr = data.get("pages_ocr", 0)
    pages_total = data.get("pages_processed", 1)

    if method == "native":
        method_label = "Native text extraction"
    elif method == "ocr":
        method_label = "OCR (scanned PDF)"
    else:
        method_label = f"Mixed ({pages_ocr} page(s) via OCR)"

    st.info(
        f"**{data['character_count']:,}** characters across "
        f"**{pages_total}** page(s) · {method_label}"
    )

    ov1, ov2 = st.columns(2)
    with ov1:
        st.markdown("**Document Type**")
        st.info(extraction.get("document_type", "Unknown"))
    with ov2:
        st.markdown("**Summary**")
        st.info(extraction.get("summary", "No summary available"))

    col_d, col_m = st.columns(2)

    with col_d:
        st.subheader("Parties")
        parties = extraction.get("parties", [])
        if parties:
            for p in parties:
                st.markdown(
                    f"- **{p['text']}** "
                    f"{'— ' + p['context'] if p.get('context') else ''}"
                )
        else:
            st.markdown("_No parties identified_")

    with col_m:
        st.subheader("Dates")
        dates = extraction.get("dates", [])
        if dates:
            for d in dates:
                st.markdown(
                    f"- **{d['text']}** "
                    f"{'— ' + d['context'] if d.get('context') else ''}"
                )
        else:
            st.markdown("_No dates identified_")

    amounts = extraction.get("monetary_amounts", [])
    if amounts:
        st.subheader("Monetary Amounts")
        for a in amounts:
            st.markdown(
                f"- **{a['text']}** "
                f"{'— ' + a['context'] if a.get('context') else ''}"
            )

    facts = extraction.get("key_facts", [])
    if facts:
        st.subheader("Key Facts")
        for fact in facts:
            st.markdown(f"- {fact}")

    if pages_ocr > 0:
        page_methods = data.get("page_methods", [])
        method_icons = {
            "native": "Native",
            "ocr": "OCR",
            "ocr_empty": "OCR (blank)",
            "ocr_failed": "OCR failed"
        }
        with st.expander(f"Per-page extraction methods ({pages_ocr} page(s) used OCR)"):
            for i, m in enumerate(page_methods, 1):
                st.markdown(f"Page {i}: {method_icons.get(m, m)}")

    with st.expander("View Raw JSON"):
        st.json(extraction)

    st.download_button(
        label="Download JSON",
        data=json.dumps(extraction, indent=2),
        file_name=f"{data['filename'].replace('.pdf', '')}_extracted.json",
        mime="application/json",
        use_container_width=True,
        key=f"dl_{data['filename']}"
    )


# Tabs: Single document vs Batch
tab_single, tab_batch = st.tabs(["Single Document", "Batch Processing"])

# ── Tab 1: Single document ─────────────────────────────────────────────────
with tab_single:
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        key="single_upload",
        help="Upload any PDF document. Text-based or scanned."
    )

    if uploaded_file is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric("Filename", uploaded_file.name)
        col2.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        col3.metric("Type", "PDF")

        st.divider()

        if st.button("Extract Information", type="primary",
                     use_container_width=True, key="btn_single"):
            with st.spinner("Processing document with local AI model..."):
                try:
                    response = requests.post(
                        f"{API_URL}/extract",
                        files={"file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )},
                        timeout=120
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Extraction complete: {uploaded_file.name}")
                        display_extraction_result(data)
                    else:
                        st.error(
                            f"Error {response.status_code}: "
                            f"{response.json().get('detail', 'Unknown error')}"
                        )
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend API.")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

# ── Tab 2: Batch processing ────────────────────────────────────────────────
with tab_batch:
    st.markdown(
        "Upload up to **20 PDF files** at once. "
        "Files are processed sequentially. "
        "One failed file does not stop the batch."
    )

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True,
        key="batch_upload",
        help="Select multiple PDF files. Maximum 20 per batch."
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        for f in uploaded_files:
            st.markdown(f"- {f.name} ({f.size / 1024:.1f} KB)")

        st.divider()

        if len(uploaded_files) > 20:
            st.error("Maximum 20 files per batch. Please reduce the selection.")
        else:
            if st.button("Extract All Documents", type="primary",
                         use_container_width=True, key="btn_batch"):

                progress_bar = st.progress(0, text="Starting batch extraction...")
                status_text = st.empty()

                try:
                    files_payload = [
                        ("files", (f.name, f.getvalue(), "application/pdf"))
                        for f in uploaded_files
                    ]

                    status_text.markdown(
                        f"Processing **{len(uploaded_files)}** documents "
                        f"sequentially via local LLM..."
                    )
                    progress_bar.progress(10, text="Sending files to backend...")

                    response = requests.post(
                        f"{API_URL}/extract-batch",
                        files=files_payload,
                        timeout=300
                    )

                    progress_bar.progress(100, text="Complete")

                    if response.status_code == 200:
                        batch_data = response.json()
                        total = batch_data["total_files"]
                        successful = batch_data["successful"]
                        failed = batch_data["failed"]

                        if failed == 0:
                            st.success(
                                f"Batch complete: {successful}/{total} documents "
                                f"extracted successfully"
                            )
                        else:
                            st.warning(
                                f"Batch complete: {successful}/{total} successful, "
                                f"{failed} failed"
                            )

                        # Summary metrics
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Files", total)
                        m2.metric("Successful", successful)
                        m3.metric("Failed", failed)

                        # Combined JSON download
                        all_successful = [
                            r for r in batch_data["results"] if r.get("success")
                        ]
                        if all_successful:
                            combined = {
                                r["filename"]: r["extraction"]
                                for r in all_successful
                            }
                            st.download_button(
                                label="Download All Results (Combined JSON)",
                                data=json.dumps(combined, indent=2),
                                file_name="batch_extraction_results.json",
                                mime="application/json",
                                use_container_width=True,
                                key="dl_batch_combined"
                            )

                        st.divider()

                        # Per-document results
                        for result in batch_data["results"]:
                            if result.get("success"):
                                with st.expander(
                                    f"✅ {result['filename']} "
                                    f"({result['pages_processed']} pages, "
                                    f"{result['character_count']:,} chars)"
                                ):
                                    display_extraction_result(result)
                            else:
                                with st.expander(
                                    f"❌ {result['filename']} — Failed"
                                ):
                                    st.error(result.get("error", "Unknown error"))

                    else:
                        st.error(
                            f"Error {response.status_code}: "
                            f"{response.json().get('detail', 'Unknown error')}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend API.")
                except requests.exceptions.Timeout:
                    st.error(
                        "Request timed out. Large batches may take several minutes. "
                        "Try with fewer files or increase the timeout."
                    )
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")