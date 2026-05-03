# app.py

import streamlit as st
import json
import time
import plotly.graph_objects as go

from backend.parser import extract_text
from backend.skills import extract_skills
from backend.matcher import match_skills
from backend.ai_validator import validate_resume


# --------------------------
# Page Setup
# --------------------------
st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume Screening System")
st.caption("Smart ATS Analyzer Powered by Gemini AI")

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
# Upload Section
# --------------------------
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


# --------------------------
# Analyze
# --------------------------
if uploaded_file:

    if st.button("🚀 Analyze Resume", use_container_width=True):

        # Extract Text
        with st.spinner("Reading uploaded file..."):
            time.sleep(1)
            resume_text = extract_text(uploaded_file)

        if not resume_text or not resume_text.strip():
            st.error("❌ Unable to extract text from file.")
            st.stop()

        # AI Resume Validation
        with st.spinner("Checking Resume Authenticity with Gemini AI..."):
            ai = validate_resume(resume_text)

        # Safe fallback if Gemini fails
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

        # Stop if file is not a resume
        elif ai.get("is_resume") is False:
            st.error("❌ Invalid Resume / Random PDF Detected")
            st.warning(ai.get("reason", "This file does not look like a valid resume."))
            st.stop()

        # ATS Analysis
        with st.spinner("Calculating ATS Score..."):
            skills = extract_skills(resume_text)

            required_skills = roles_data[selected_role]

            score, matched, missing = match_skills(
                skills,
                required_skills
            )

        st.success("✅ Analysis Completed Successfully")
        st.write("---")

        # Candidate Info
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

        # Score
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

        # Chart
        st.subheader("📈 Skill Breakdown")

        fig = go.Figure(data=[go.Pie(
            labels=["Matched Skills", "Missing Skills"],
            values=[len(matched), len(missing)],
            hole=0.55
        )])

        fig.update_layout(title="Matched vs Missing Skills")
        st.plotly_chart(fig, use_container_width=True)

        # Skills
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

else:
    st.info("📤 Upload a resume to begin.")