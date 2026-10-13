"""Start with: streamlit run app.py"""

import csv
import io
import json
from pathlib import Path

import streamlit as st

from extractor import ai_extract, python_extract, read_pdf



st.set_page_config(page_title="Demo Information Extractor", layout="wide")
st.title("Demo Extractor")
st.caption("Small portfolio demo •This prototype is designed to extract structured information from Technical Data Sheet PDFs; other PDFs can be uploaded in AI mode, but their information may not be extracted correctly ")

SAMPLES = Path(__file__).parent / "samples"
PDF_FILES = sorted(SAMPLES.glob("*.pdf"))
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

left, right = st.columns([1, 1.2], gap="large")

with left:
    st.subheader("1. Choose a PDF")
    sample_name = st.selectbox("Included examples", [file.name for file in PDF_FILES])
    uploaded_file = st.file_uploader("Or upload a PDF (overrides example)", type=["pdf"])
    if uploaded_file is not None:
        pdf_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
    else:
        pdf_bytes = (SAMPLES / sample_name).read_bytes() if PDF_FILES else b""
        filename = sample_name

    st.caption(f"Selected: {filename} | Demo limit: 5 pages, 12 MB")
    st.subheader("2. Extraction mode")
    mode = st.radio("Mode", ["Python / Regex", "AI / LLM"], horizontal=True)

    if mode == "AI / LLM":
        model = st.text_input("Gemini model ID", value=DEFAULT_GEMINI_MODEL)
        api_key = st.text_input("Gemini API key", type="password")
        vision = st.checkbox(
            "Include page images (can read graphs approximately)",
            value=True,
        )
        st.caption("This app uses Google Gemini only. Vision requires a vision-capable model and may cost more.")
    else:
        model, api_key, vision = "", "", False

    run = st.button("Extract Information", type="primary", use_container_width=True)

with right:
    st.subheader("3. Structured output")
    if run:
        if not pdf_bytes:
            st.error("Please choose a PDF.")
        elif len(pdf_bytes) > 12 * 1024 * 1024:
            st.error("PDF exceeds the 12 MB demo limit.")
        else:
            try:
                with st.spinner("Reading PDF and extracting information..."):
                    texts, page_images = read_pdf(pdf_bytes)
                    if mode == "Python / Regex":
                        result = python_extract(texts)
                    else:
                        result = ai_extract(texts, page_images, model, api_key, vision)
                st.success(f"Extracted from {len(texts)} page(s) using {mode}.")
                st.session_state["result"] = result.model_dump(mode="json")
                st.session_state["result_file"] = filename
                st.session_state["result_mode"] = mode
            except Exception as error:
                st.error(f"Extraction failed: {error}")

    if "result" not in st.session_state:
        st.info("Choose one of the sample PDFs or upload your own, then click Extract Information.")
    else:
        output = st.session_state["result"]
        st.caption(f"Last result: {st.session_state['result_file']} | {st.session_state['result_mode']}")
        st.markdown("**Product**")
        st.json({key: output.get(key) for key in
                 ["product_name", "product_code", "manufacturer", "category"]}, expanded=True)

        st.markdown(f"**Technical properties ({len(output['properties'])})**")
        if output["properties"]:
            st.dataframe(output["properties"], use_container_width=True, hide_index=True)
        else:
            st.warning("No properties matched or were identified.")

        st.markdown(f"**Extracted graph points ({len(output['graphs'])} graph(s))**")
        if output["graphs"]:
            for graph in output["graphs"]:
                st.write(f"{graph['title']} — page {graph.get('source_page', '?')}")
                st.dataframe(graph["points"], hide_index=True, use_container_width=True)
                st.caption("Graph values estimated by the model; verify against the PDF.")
        else:
            st.caption("No graph points extracted. Python mode cannot interpret chart images.")

        for note in output.get("notes", []):
            st.caption("• " + note)

        st.download_button(
            "Download structured JSON",
            data=json.dumps(output, indent=2, ensure_ascii=False),
            file_name="extracted_data.json", mime="application/json",
        )
        if output["properties"]:
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=output["properties"][0].keys())
            writer.writeheader()
            writer.writerows(output["properties"])
            st.download_button(
                "Download properties CSV", data=buffer.getvalue(),
                file_name="technical_properties.csv", mime="text/csv",
            )
