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

    /* Primary Action Button - Architect */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
        padding: 10px;
        font-size: 1.1em;
    }

    /* Download Buttons Visibility */
    div.stDownloadButton > button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        width: 100%;
        font-weight: bold !important;
    }
    
    .signature { color: #c084fc; font-weight: bold; text-align: center; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# --- Engine Initialization ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

# API Key Check
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing in Streamlit Secrets.")
    st.stop()

# Load Engines
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
        # Step 1: Display Image
        image_preview = Image.open(uploaded_file)
        st.image(image_preview, caption="Target Image", use_container_width=True)
        
        # Step 2: RESET file pointer for OpenCV processing
        uploaded_file.seek(0)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Analyzing and Structuring..."):
                try:
                    # OpenCV decoding
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                    if img is None:
                        st.error
