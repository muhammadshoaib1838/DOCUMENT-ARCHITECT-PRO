import streamlit as st
import easyocr
import cv2
import numpy as np
from groq import Groq
from docx import Document
import os
from PIL import Image

# --- Page Configuration ---
st.set_page_config(page_title="Document Architect Pro", layout="wide")

# --- CSS for Visibility and Style ---
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    
    /* Jaman Tagline Style */
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

    /* Fixing Button Visibility (Dark text on bright button) */
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        width: 100%;
        height: 3em;
    }
    
    .signature { color: #c084fc; font-weight: bold; text-align: center; margin-top: 50px; font-family: 'serif'; }
    </style>
    """, unsafe_allow_html=True)

# --- API Key Handling ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# --- Initialize Engines ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

if not GROQ_API_KEY:
    st.error("❌ API Key Missing: Please add GROQ_API_KEY to your Streamlit Secrets.")
    st.stop()

reader = load_ocr()
client = Groq(api_key=GROQ_API_KEY)

# --- Header ---
st.title("🌌 DOCUMENT ARCHITECT PRO")
st.markdown('<div class="jaman-tagline">Transforming handwritten chaos into structured digital gold.</div>', unsafe_allow_html=True)

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📸 Upload Source")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Show preview
        image_preview = Image.open(uploaded_file)
        st.image(image_preview, caption="Target Image", use_container_width=True)
        
        if st.button("ARCHITECT DOCUMENT ✨"):
            with st.spinner("Analyzing text..."):
                try:
                    # SECURE IMAGE LOADING: Convert to bytes safely for OpenCV
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                    if img is None:
                        st.error("Failed to decode image. Try another format.")
                    else:
                        # 1. OCR Process
                        raw_text = " ".join(reader.readtext(img, detail=0))
                        
                        if not raw_text.strip():
                            st.warning("No text found in the image.")
                        else:
                            # 2. AI Structuring
                            prompt = f"Act as a Document Architect. Format this OCR text into a professional document with Markdown. End with '--- FINAL SUMMARY ---'. TEXT: {raw_text}"
                            completion = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model="llama-3.3-70b-versatile"
                            )
                            full_output = completion.choices[0].message.content
                            
                            # Split logic
                            if "--- FINAL SUMMARY ---" in full_output:
                                notes, summary = full_output.split("--- FINAL SUMMARY ---")
                            else:
                                notes, summary = full_output, "Summary integrated in text."

                            # Store results
                            st.session_state.processed = {"notes": notes, "summary": summary, "raw": raw_text}
                            st.session_state.history.append(f"Note {len(st.session_state.history)+1}: {notes[:30]}...")
                            
                            # Create DOCX
                            doc = Document()
                            doc.add_heading('Document Architect Export', 0)
                            doc.add_paragraph(notes)
                            doc.save("Architect_Export.docx")

                except Exception as e:
                    st.error(f"Processing Error: {str(e)}")

# --- Results Area ---
with col2:
    if "processed" in st.session_state:
        tab1, tab2, tab3 = st.tabs(["✨ Digital Blueprint", "💡 Executive Summary", "📄 Raw OCR Buffer"])
        
        with tab1:
            st.markdown(st.session_state.processed["notes"])
            with open("Architect_Export.docx", "rb") as f:
                st.download_button("📥 Download DOCX", f, file_name="Architect_Export.docx")
        
        with tab2:
            st.info(st.session_state.processed["summary"])
            
        with tab3:
            st.text_area("Initial Scan Data", st.session_state.processed["raw"], height=400)
    else:
        st.info("Upload an image and click 'Architect' to see the results here.")

# --- Footer ---
st.sidebar.subheader("🕒 Session History")
for h in st.session_state.history:
    st.sidebar.text(h)

st.markdown('<div class="signature">DESIGNED & ENGINEERED BY<br>Muhammad Shoaib Nazz</div>', unsafe_allow_html=True)
