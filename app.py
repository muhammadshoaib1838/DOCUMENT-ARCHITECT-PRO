import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from PIL import Image

# --- Page Configuration ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- CSS for Visibility & High-Contrast ---
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

    /* Fix Download Button Visibility (White text on blue border) */
    div.stDownloadButton > button {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
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

# Secure API Key Check
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ API Key Missing: Please add GROQ_API_KEY to your Streamlit Secrets.")
    st.stop()

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- UI Layout ---
st.title("🌌 DOCUMENT ARCHITECT PRO")
st.markdown('<div class="jaman-tagline">Transforming handwritten chaos into structured digital gold.</div>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📸 Upload Source")
