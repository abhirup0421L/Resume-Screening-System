# app.py

import streamlit as st
import json
import time
import plotly.graph_objects as go
from fpdf import FPDF

from backend.parser import extract_text
from backend.skills import extract_skills
from backend.matcher import match_skills
from backend.ai_validator import validate_resume
from backend.resume_generator import generate_resume


# --------------------------
# Page Setup
# --------------------------
st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "page" not in st.session_state:
    st.session_state.page = "Resume Analyzer"


# --------------------------
# Custom CSS
# --------------------------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #020617, #0F172A);
}

/* Sidebar Design */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #111827, #0F172A);
    border-right: 1px solid rgba(255,255,255,0.08);
}

.sidebar-title {
    font-size: 30px;
    font-weight: 900;
    color: #FFFFFF;
    margin-bottom: 5px;
}

.sidebar-subtitle {
    color: #94A3B8;
    font-size: 14px;
    margin-bottom: 25px;
}

.sidebar-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 18px;
    margin-bottom: 18px;
}

/* Main Header */
.main-title {
    font-size: 45px;
    font-weight: 900;
    color: #FFFFFF;
}

.main-subtitle {
    font-size: 17px;
    color: #94A3B8;
    margin-bottom: 25px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #06B6D4, #3B82F6);
    color: white;
    border: none;
    border-radius: 14px;
    height: 48px;
    font-weight: 800;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0px 6px 20px rgba(59,130,246,0.35);
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background: #1E293B;
    border: 1px solid rgba(255,255,255,0.08);
    color: white;
    height: 52px;
    border-radius: 16px;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(90deg, #06B6D4, #3B82F6);
}

/* Download Buttons */
.stDownloadButton > button {
    background: linear-gradient(90deg, #0EA5E9, #2563EB);
    color: white;
    border: none;
    border-radius: 14px;
    height: 48px;
    font-weight: 800;
}

/* Metrics */
div[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.04);
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
}

textarea, input {
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)


# --------------------------
# Sidebar Navigation
# --------------------------
with st.sidebar:

    st.markdown('<div class="sidebar-title">⚡ Resume AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-subtitle">AI Resume Analyzer & CV Maker</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.write("📌 **Navigation**")

    if st.button("🔍 Resume Analyzer", use_container_width=True):
        st.session_state.page = "Resume Analyzer"
        st.rerun()

    if st.button("✨ AI CV Maker", use_container_width=True):
        st.session_state.page = "AI CV Maker"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.success(f"Active: {st.session_state.page}")

    st.markdown("---")

    st.info("Click the arrow on top-left sidebar to open/close navigation.")


# --------------------------
# Header
# --------------------------
st.markdown(
    '<div class="main-title">📄 AI Resume Screening System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">Smart ATS Analyzer + AI CV Maker Powered by Gemini AI</div>',
    unsafe_allow_html=True
)

st.write("---")


# --------------------------
# Load Roles
# --------------------------
try:
    with open("data/roles.json", "r") as file:
        roles_data = json.load(file)
except FileNotFoundError:
    st.error("❌ data/roles.json file not found.")
    st.stop()

job_roles = list(roles_data.keys())

if not job_roles:
    st.error("❌ No job roles found in roles.json.")
    st.stop()


# --------------------------
# PDF Generator
# --------------------------
def create_pdf(resume_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)

    for line in resume_text.split("\n"):
        clean_line = line.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 8, clean_line)

    return pdf.output(dest="S").encode("latin-1")


# =====================================================
# PAGE 1: RESUME ANALYZER
# =====================================================
if st.session_state.page == "Resume Analyzer":

    st.header("🔍 Resume Analysis")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Resume",
            type=["pdf", "docx", "txt"]
        )

    with col2:
        selected_role = st.selectbox(
            "🎯 Select Job Role",
            job_roles
        )

    if uploaded_file:

        if st.button("🚀 Analyze Resume", use_container_width=True):

            with st.spinner("Reading uploaded file..."):
                time.sleep(1)
                resume_text = extract_text(uploaded_file)

            if not resume_text or not resume_text.strip():
                st.error("❌ Unable to extract text from file.")
                st.stop()

            with st.spinner("Checking Resume Authenticity with Gemini AI..."):
                ai = validate_resume(resume_text)

            if ai.get("is_resume") is None:
                st.warning("⚠️ Gemini AI unavailable. Running normal ATS scan only.")

                ai = {
                    "is_resume": True,
                    "candidate_name": "Unknown",
                    "experience_level": "Unknown",
                    "confidence": 0,
                    "summary": "AI validation was unavailable. Only normal ATS skill matching was performed.",
                    "reason": "Gemini AI unavailable"
                }

            elif ai.get("is_resume") is False:
                st.error("❌ Invalid Resume / Random PDF Detected")
                st.warning(ai.get("reason", "This file does not look like a valid resume."))
                st.stop()

            with st.spinner("Calculating ATS Score..."):
                skills = extract_skills(resume_text)
                required_skills = roles_data[selected_role]
                score, matched, missing = match_skills(skills, required_skills)

            st.success("✅ Analysis Completed Successfully")
            st.write("---")

            st.subheader("👤 Candidate Details")

            a, b, c = st.columns(3)

            with a:
                st.metric("Name", ai.get("candidate_name", "Unknown"))

            with b:
                st.metric("Experience", ai.get("experience_level", "Unknown"))

            with c:
                st.metric("AI Confidence", f'{ai.get("confidence", 0)}%')

            st.info(ai.get("summary", "No AI summary available."))

            st.write("---")

            st.subheader("📊 ATS Score")

            s1, s2 = st.columns(2)

            with s1:
                st.metric("Match Score", f"{score}%")
                st.progress(score / 100)

            with s2:
                if score >= 85:
                    st.success("Excellent Match ✅")
                elif score >= 65:
                    st.warning("Good Match 👍")
                else:
                    st.error("Needs Improvement ❌")

            st.subheader("📈 Skill Breakdown")

            fig = go.Figure(data=[go.Pie(
                labels=["Matched Skills", "Missing Skills"],
                values=[len(matched), len(missing)],
                hole=0.55
            )])

            fig.update_layout(title="Matched vs Missing Skills")
            st.plotly_chart(fig, use_container_width=True)

            x, y = st.columns(2)

            with x:
                st.subheader("✅ Matched Skills")
                if matched:
                    for skill in matched:
                        st.success(skill.title())
                else:
                    st.info("No matched skills found.")

            with y:
                st.subheader("❌ Missing Skills")
                if missing:
                    for skill in missing:
                        st.error(skill.title())
                else:
                    st.success("No missing skills.")

            st.write("---")

            st.subheader("📝 Need a Better Resume?")
            st.info("Use the AI CV Maker section to generate a professional ATS-friendly resume.")

            if st.button("✨ Go to AI CV Maker", use_container_width=True):
                st.session_state.page = "AI CV Maker"
                st.rerun()

    else:
        st.info("📤 Upload a resume to begin.")

        st.write("---")
        st.subheader("Don’t have a resume?")
        if st.button("✨ Create Resume with AI", use_container_width=True):
            st.session_state.page = "AI CV Maker"
            st.rerun()


# =====================================================
# PAGE 2: AI CV MAKER
# =====================================================
elif st.session_state.page == "AI CV Maker":

    st.header("✨ AI CV Maker")
    st.caption("Enter your details and Gemini will generate a professional ATS-friendly resume.")

    with st.form("cv_maker_form"):

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")

        target_role = st.selectbox("Target Job Role", job_roles, key="cv_role")

        education = st.text_area(
            "Education",
            placeholder="Example: B.Tech CSE, SurTech, MAKAUT, 2026"
        )

        skills = st.text_area(
            "Skills",
            placeholder="Example: Python, Java, SQL, Machine Learning, Streamlit"
        )

        experience = st.text_area(
            "Experience",
            placeholder="Example: Internship, freelance work, training, or write Fresher"
        )

        projects = st.text_area(
            "Projects",
            placeholder="Example: Resume Screening System using Python and Streamlit"
        )

        submitted = st.form_submit_button("🚀 Generate CV", use_container_width=True)

    if submitted:

        if not name or not email or not skills or not education:
            st.error("Please fill at least Name, Email, Education, and Skills.")
            st.stop()

        with st.spinner("Generating professional resume with Gemini..."):
            generated_resume = generate_resume(
                name=name,
                email=email,
                phone=phone,
                education=education,
                skills=skills,
                experience=experience,
                projects=projects,
                target_role=target_role
            )

        st.session_state.generated_resume = generated_resume
        st.session_state.generated_name = name

    if "generated_resume" in st.session_state:

        generated_resume = st.session_state.generated_resume
        name = st.session_state.generated_name

        st.success("✅ Resume Generated Successfully")
        st.write("---")

        st.subheader("📄 Generated Resume")

        st.text_area(
            "Your AI Generated Resume",
            generated_resume,
            height=500
        )

        pdf_data = create_pdf(generated_resume)

        btn1, btn2 = st.columns(2)

        with btn1:
            st.download_button(
                label="⬇️ Download Resume as TXT",
                data=generated_resume,
                file_name=f"{name.replace(' ', '_')}_resume.txt",
                mime="text/plain",
                use_container_width=True
            )

        with btn2:
            st.download_button(
                label="📄 Download Resume as PDF",
                data=pdf_data,
                file_name=f"{name.replace(' ', '_')}_resume.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.write("---")

        if st.button("🔍 Analyze This Resume", use_container_width=True):
            st.session_state.page = "Resume Analyzer"
            st.rerun()
