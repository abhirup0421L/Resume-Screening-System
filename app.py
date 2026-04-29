# app.py

import streamlit as st

st.set_page_config(
    page_title="AI Resume Screening System",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Screening System")
st.subheader("Smart Resume Analyzer using Python + Streamlit")

st.write("""
Welcome to the AI Resume Screening Project.

### Features:
✅ Upload Resume (PDF / DOCX / TXT)  
✅ Extract Resume Skills  
✅ Compare with Selected Job Role  
✅ Generate ATS Match Score  
✅ Show Missing Skills  
✅ Give Improvement Suggestions  

Use the left sidebar to navigate pages.
""")

st.info("Go to Upload page to start analysis.")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.success("Select a page")