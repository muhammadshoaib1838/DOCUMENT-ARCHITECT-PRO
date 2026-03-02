import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- Page Config ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- API Key handling ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Initialize Engines ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- Custom Styling ---
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

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🕒 Session History")
    for item in st.session_state.history:
        st.write(item)

# --- Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    uploaded_file = st.file_uploader("📸 Upload Source", type=["jpg", "jpeg", "png"])
    submit_btn = st.button("ARCHITECT DOCUMENT ✨")

if uploaded_file and submit_btn:
    with st.spinner("Processing..."):
        try:
            # FIX 1: Use np.uint8 to avoid NameError
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            
            # OCR Processing
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed_img = cv2.adaptiveThreshold(
                cv2.GaussianBlur(gray, (5, 5), 0),
                255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            raw_results = reader.readtext(processed_img, detail=0)
            raw_text = " ".join(raw_results)

            if raw_text.strip():
                # FIX 2: Cleaned multi-line string to avoid SyntaxError
                prompt = (
                    "Act as a Professional Document Architect. "
                    "Convert this OCR text into a beautiful digital document: "
                    "- Use # for the Main Title "
                    "- Use ## for Section Headings "
                    "- Use bolding (**) for important technical terms "
                    "- End with a section titled '--- FINAL SUMMARY ---' "
                    f"TEXT: {raw_text}"
                )

                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile"
                )
                full_output = chat.choices[0].message.content

                if "--- FINAL SUMMARY ---" in full_output:
                    notes, summary = full_output.split("--- FINAL SUMMARY ---")
                else:
                    notes, summary = full_output, "Summary included in text."

                # Update State
                st.session_state.history.append(f"Document {len(st.session_state.history)+1}")

                with col2:
                    t1, t2, t3 = st.tabs(["✨ Blueprint", "💡 Summary", "📄 Raw"])
                    with t1:
                        st.markdown(notes)
                        # DOCX Export logic
                        doc = Document()
                        doc.add_paragraph(notes)
                        doc.save("output.docx")
                        with open("output.docx", "rb") as f:
                            st.download_button("Download DOCX", f, "Architect_Export.docx")
                    with t2:
                        st.write(summary.strip())
                    with t3:
                        st.text_area("OCR Data", raw_text, height=200)
            else:
                st.warning("No text found in image.")
        except Exception as e:
            st.error(f"Processing Error: {e}")

# --- Footer ---
st.markdown("""
    <div class="signature-name">Muhammad Shoaib Nazz</div>
    """, unsafe_allow_html=True)
