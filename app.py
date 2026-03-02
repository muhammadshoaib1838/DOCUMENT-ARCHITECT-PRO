import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
from docx import Document
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

    /* Primary Action Button (Architect) */
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

    /* Download Buttons Visibility Fix */
    div.stDownloadButton > button {
        background-color: #1e293b !important;
        color: #38bdf8 !important; /* Bright Blue text */
        border: 1px solid #38bdf8 !important;
        font-weight: bold !important;
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
        # Step 1: Display Preview
        image_preview = Image.open(uploaded_file)
        st.image(image_preview, caption="Preview", use_container_width=True)
        
        # FIX: Reset pointer so OpenCV can read the file buffer
        uploaded_file.seek(0)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Processing..."):
                try:
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                    if img is None:
                        st.error("Error decoding image.")
                    else:
                        # 1. OCR
                        raw_text = " ".join(reader.readtext(img, detail=0))
                        
                        # 2. AI Architecture
                        prompt = f"Format this text into a professional document with Markdown. End with '--- FINAL SUMMARY ---'. TEXT: {raw_text}"
                        chat = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )
                        full_output = chat.choices[0].message.content
                        
                        notes, summary = full_output.split("--- FINAL SUMMARY ---") if "--- FINAL SUMMARY ---" in full_output else (full_output, "Summary included.")

                        st.session_state.processed = {"notes": notes, "summary": summary, "raw": raw_text}
                        st.session_state.history.append(f"Note {len(st.session_state.history)+1}: {notes[:30]}...")

                        # 3. Generate DOCX
                        doc = Document()
                        doc.add_heading('Architect Export', 0)
                        doc.add_paragraph(notes)
                        doc_io = io.BytesIO()
                        doc.save(doc_io)
                        st.session_state.docx_data = doc_io.getvalue()

                        # 4. Generate PDF
                        pdf_io = io.BytesIO()
                        c = canvas.Canvas(pdf_io, pagesize=letter)
                        c.setFont("Helvetica-Bold", 16)
                        c.drawString(50, 750, "Document Architect Export")
                        c.setFont("Helvetica", 10)
                        y = 720
                        for line in notes.split('\n'):
                            if y < 50: # Simple pagination
                                c.showPage()
                                y = 750
                            c.drawString(50, y, line[:95])
                            y -= 15
                        c.save()
                        st.session_state.pdf_data = pdf_io.getvalue()

                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    if "processed" in st.session_state:
        tab1, tab2, tab3 = st.tabs(["✨ Digital Blueprint", "💡 Executive Summary", "📄 Raw OCR Buffer"])
        
        with tab1:
            st.markdown(st.session_state.processed["notes"])
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
