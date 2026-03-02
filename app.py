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

# --- Page Configuration ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- CSS for High-Contrast "Jaman" Styling ---
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
        font-size: 1.2em;
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 20px;
    }
    .signature { color: #c084fc; font-weight: bold; text-align: center; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- API Key Handling (Streamlit Secret Format) ---
# This looks for the key in Streamlit's Secret management system
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not found! Please add it to your Streamlit Secrets.")
    st.stop()

# --- Initialize Engines ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- Header ---
st.title("🌌 DOCUMENT ARCHITECT PRO")
st.markdown('<div class="jaman-tagline">Transforming handwritten chaos into structured digital gold.</div>', unsafe_allow_html=True)

# --- Sidebar History ---
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("🕒 Session History")
    for entry in st.session_state.history:
        st.info(entry)

# --- Main Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📸 Upload Source")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Processing..."):
                try:
                    # 1. OCR Process
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, 1)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    raw_text = " ".join(reader.readtext(gray, detail=0))

                    if not raw_text.strip():
                        st.error("No text detected in image.")
                    else:
                        # 2. AI Structuring
                        prompt = f"Convert this OCR text into a professional document with headings and bold terms. End with '--- FINAL SUMMARY ---'. TEXT: {raw_text}"
                        chat = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )
                        full_output = chat.choices[0].message.content
                        
                        if "--- FINAL SUMMARY ---" in full_output:
                            notes, summary = full_output.split("--- FINAL SUMMARY ---")
                        else:
                            notes, summary = full_output, "Included in text."

                        # 3. Save to Session State
                        st.session_state.notes = notes
                        st.session_state.summary = summary
                        st.session_state.raw = raw_text
                        st.session_state.history.append(f"Note {len(st.session_state.history)+1}: {notes[:20]}...")

                        # 4. Generate Files
                        doc = Document()
                        doc.add_heading('Architect Export', 0)
                        doc.add_paragraph(notes)
                        doc.save("export.docx")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Results Area ---
with col2:
    if "notes" in st.session_state:
        tab1, tab2, tab3 = st.tabs(["✨ Digital Blueprint", "💡 Executive Summary", "📄 Raw OCR"])
        
        with tab1:
            st.markdown(st.session_state.notes)
            with open("export.docx", "rb") as f:
                st.download_button("Download DOCX", f, file_name="Architect_Export.docx")
        
        with tab2:
            st.write(st.session_state.summary)
            
        with tab3:
            st.text_area("OCR Result", st.session_state.raw, height=300)

st.markdown('<div class="signature">DESIGNED & ENGINEERED BY<br>Muhammad Shoaib Nazz</div>', unsafe_allow_html=True)
