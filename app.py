import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
from docx import Document
# NEW: Import ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from PIL import Image
import io

# --- Page Configuration ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- CSS for High-Contrast & Button Visibility ---
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    
    .jaman-tagline {
        background-color: #4c0519;
        color: #ffff00 !important;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: 900;
        font-size: 1.2em;
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 25px;
    }

    /* Fixed Button: High visibility white text on purple gradient */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
        padding: 10px;
        font-size: 1.1em;
        text-transform: uppercase;
    }
    
    /* Style for download buttons to distinguish them */
    div.stDownloadButton > button {
        background-color: #1e293b !important;
        border: 1px solid #4f46e5 !important;
        color: white !important;
    }
    
    .signature { color: #c084fc; font-weight: bold; text-align: center; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- API Key Handling ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing in Streamlit Secrets.")
    st.stop()

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- UI Header ---
st.title("🌌 DOCUMENT ARCHITECT PRO")
st.markdown('<div class="jaman-tagline">Transforming handwritten chaos into structured digital gold.</div>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📸 Upload Source")
    uploaded_file = st.file_uploader("Drop image here", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image_preview = Image.open(uploaded_file)
        st.image(image_preview, caption="Preview", use_container_width=True)
        
        uploaded_file.seek(0)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Converting chaos to gold..."):
                try:
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                    if img is None:
                        st.error("Error decoding image.")
                    else:
                        raw_text = " ".join(reader.readtext(img, detail=0))
                        
                        if not raw_text.strip():
                            st.warning("No text detected.")
                        else:
                            prompt = f"Convert this text into a professional document with Markdown headings. End with '--- FINAL SUMMARY ---'. TEXT: {raw_text}"
                            chat = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.3-70b-versatile"
                            )
                            full_output = chat.choices[0].message.content
                            
                            notes, summary = full_output.split("--- FINAL SUMMARY ---") if "--- FINAL SUMMARY ---" in full_output else (full_output, "Summary included in text.")

                            st.session_state.processed = {"notes": notes, "summary": summary, "raw": raw_text}
                            st.session_state.history.append(f"Note {len(st.session_state.history)+1}: {notes[:30]}...")

                            # --- DOCX Generation ---
                            doc = Document()
                            doc.add_heading('Architect Export', 0)
                            doc.add_paragraph(notes)
                            doc_io = io.BytesIO()
                            doc.save(doc_io)
                            st.session_state.docx_data = doc_io.getvalue()
