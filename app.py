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

    /* Primary Action Button */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
        padding: 10px;
    }

    /* Download Buttons - Forced White Text */
    div.stDownloadButton > button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        width: 100%;
    }
    
    .signature { color: #c084fc; font-weight: bold; text-align: center; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- Engine Initialization ---
@st.cache_resource
def load_ocr():
    # Only loads once to save memory
    return easyocr.Reader(['en'], gpu=False)

# API Key Check
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing in Streamlit Secrets. Please add it in Settings.")
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
    uploaded_file = st.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Show Preview
        image_preview = Image.open(uploaded_file)
        st.image(image_preview, caption="Target Image", use_container_width=True)
        
        # CRITICAL: Reset pointer for OpenCV
        uploaded_file.seek(0)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Analyzing and Structuring..."):
                try:
                    # OpenCV decoding
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                    if img is None:
                        st.error("Failed to decode image data.")
                    else:
                        # 1. OCR Analysis
                        raw_text = " ".join(reader.readtext(img, detail=0))
                        
                        if not raw_text.strip():
                            st.warning("No readable text found in image.")
                        else:
                            # 2. AI Structuring
                            prompt = f"Convert this text into a structured professional document using Markdown. Finish with '--- FINAL SUMMARY ---'. TEXT: {raw_text}"
                            chat = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.3-70b-versatile"
                            )
                            full_output = chat.choices[0].message.content
                            
                            # Content Splitting
                            if "--- FINAL SUMMARY ---" in full_output:
                                notes, summary = full_output.split("--- FINAL SUMMARY ---")
                            else:
                                notes, summary = full_output, "Summary included in main text."

                            # 3. Generate DOCX (In Memory)
                            doc = Document()
                            doc.add_heading('Document Architect Export', 0)
                            doc.add_paragraph(notes)
                            docx_io = io.BytesIO()
                            doc.save(docx_io)
                            docx_bytes = docx_io.getvalue()
                            
                            # 4. Generate PDF (In Memory)
                            pdf_io = io.BytesIO()
                            c = canvas.Canvas(pdf_io, pagesize=letter)
                            c.setFont("Helvetica-Bold", 14)
                            c.drawString(50, 750, "Document Architect Export")
                            c.setFont("Helvetica", 10)
                            y_pos = 720
                            for line in notes.split('\n'):
                                if y_pos < 50:
                                    c.showPage()
                                    y_pos = 750
                                c.drawString(50, y_pos, line[:95])
                                y_pos -= 15
                            c.save()
                            pdf_bytes = pdf_io.getvalue()

                            # Store everything in session state
                            st.session_state.processed = {
                                "notes": notes.strip(),
                                "summary": summary.strip(),
                                "raw": raw_text,
                                "docx": docx_bytes,
                                "pdf": pdf_bytes
                            }
                            st.session_state.history.append(f"Scan {len(st.session_state.history)+1}: {notes[:25]}...")

                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")

# --- Results Display ---
with col2:
    if "processed" in st.session_state:
        tab1, tab2, tab3 = st.tabs(["✨ Digital Blueprint", "💡 Executive Summary", "📄 Raw OCR"])
        
        with tab1:
            st.markdown(st.session_state.processed["notes"])
            st.divider()
            
            # Action Buttons - Corrected Indentation
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                st.download_button(
                    label="📥 Download DOCX",
                    data=st.session_state.processed["docx"],
                    file_name="Architect_Export.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            with dcol2:
                st.download_button(
                    label="📥 Download PDF",
                    data=st.session_state.processed["pdf"],
                    file_name="Architect_Export.pdf",
                    mime="application/pdf"
                )
        
        with tab2:
            st.info(st.session_state.processed["summary"])
            
        with tab3:
            st.text_area("OCR Scanned Data", st.session_state.processed["raw"], height=300)
    else:
        st.info("Upload an image and click 'Architect' to begin.")

# --- Footer ---
st.sidebar.subheader("🕒 Session History")
for item in st.session_state.history:
    st.sidebar.write(item)

st.markdown('<div class="signature">DESIGNED & ENGINEERED BY<br>Muhammad Shoaib Nazz</div>', unsafe_allow_html=True)
