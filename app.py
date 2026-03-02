import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

# --- Page Config ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- API Key handling ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Initialize Engines (Cached for performance) ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- Custom Styling (Matching your Jaman & Dark Navy theme) ---
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    .jaman-tagline {
        background-color: #4c0519; 
        color: #ffff00;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-weight: 900;
        font-size: 1.3em;
        margin-bottom: 25px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .signature-name {
        color: #c084fc;
        font-size: 1.6em;
        font-family: serif;
        font-weight: bold;
        text-align: center;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>🌌 DOCUMENT ARCHITECT PRO</h1>", unsafe_allow_html=True)
st.markdown('<div class="jaman-tagline">Transforming handwritten chaos into structured digital gold.</div>', unsafe_allow_html=True)

# --- Sidebar History ---
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.markdown("### 🕒 Session History")
    for item in st.session_state.history:
        st.write(item)

# --- Main Logic ---
col1, col2 = st.columns([1, 2])

with col1:
    uploaded_file = st.file_uploader("📸 Upload Source", type=["jpg", "jpeg", "png"])
    submit_btn = st.button("ARCHITECT DOCUMENT ✨")

if uploaded_file and submit_btn:
    with st.spinner("Architecting your document..."):
        # Convert uploaded file to OpenCV format
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=uint8)
        img = cv2.imdecode(file_bytes, 1)
        
        # 1. Image Preprocessing & OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        processed_img = cv2.adaptiveThreshold(
            cv2.GaussianBlur(gray, (5, 5), 0),
            255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        raw_text = " ".join(reader.readtext(processed_img, detail=0))

        if raw_text.strip():
            # 2. AI Structuring (Groq)
            prompt = f"""
            Act as a Professional Document Architect.
            Convert this OCR text into a beautiful digital document:
            - Use # for the Main Title
            - Use ## for Section Headings
            - Use bolding (**) for important technical terms
            - End with a section titled '--- FINAL SUMMARY ---'
            TEXT: {raw_text}
            """

            chat = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile"
            )
            full_output = chat.choices[0].message.content

            if "--- FINAL SUMMARY ---" in full_output:
                notes, summary = full_output.split("--- FINAL SUMMARY ---")
            else:
                notes, summary = full_output, "Summary included in text."

            # Update History
            st.session_state.history.append(f"Note {len(st.session_state.history) + 1}: {notes[:20]}...")

            # 3. Display Results
            with col2:
                tab1, tab2, tab3 = st.tabs(["✨ Digital Blueprint", "💡 Executive Summary", "📄 Raw OCR Buffer"])
                
                with tab1:
                    st.markdown(notes)
                    
                    # File Exports
                    doc_path = "Architect_Export.docx"
                    d = Document()
                    d.add_heading('Document Architect Pro Export', 0)
                    d.add_paragraph(notes)
                    d.save(doc_path)
                    
                    with open(doc_path, "rb") as f:
                        st.download_button("Download DOCX", f, file_name=doc_path)

                with tab2:
                    st.write(summary.strip())

                with tab3:
                    st.code(raw_text)
        else:
            st.error("❌ No text detected.")

# --- Footer ---
st.markdown(f"""
    <div style="border-top: 1px solid #1e293b; padding: 20px;">
        <p style="text-align: center; color: #94a3b8;">DESIGNED & ENGINEERED BY</p>
        <div class="signature-name">Muhammad Shoaib Nazz</div>
    </div>
    """, unsafe_allow_html=True)
