# app.py (All Features in One Page)

import streamlit as st
import json
import time
import plotly.graph_objects as go

from backend.parser import extract_text
from backend.skills import extract_skills
from backend.matcher import match_skills

st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide"
)

# Header
st.title("📄 AI Resume Screening System")
st.subheader("Upload Resume and Get ATS Score Instantly")

st.write("---")

# Load Roles
with open("data/roles.json", "r") as file:
    roles_data = json.load(file)

job_roles = list(roles_data.keys())

# Upload Section
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "📤 Upload Resume",
        type=["pdf", "docx", "txt"]
    )

with col2:
    job_role = st.selectbox(
        "🎯 Select Job Role",
        job_roles
    )

# Analyze Button
if uploaded_file is not None:

    if st.button("🔍 Analyze Resume", use_container_width=True):

        with st.spinner("Analyzing Resume..."):
            time.sleep(2)

            resume_text = extract_text(uploaded_file)

            candidate_skills = extract_skills(resume_text)

            score, matched, missing = match_skills(candidate_skills, job_role)

        st.success("Analysis Completed ✅")

        st.write("---")

        # Result Section
        st.header("📊 Resume Analysis Result")

        col3, col4 = st.columns(2)

        with col3:
            st.metric("ATS Match Score", f"{score}%")
            st.progress(score / 100)

        with col4:
            if score >= 85:
                st.success("Excellent Candidate Match ✅")
            elif score >= 65:
                st.warning("Good Candidate Match 👍")
            else:
                st.error("Needs Improvement ❌")

        # Pie Chart
        fig = go.Figure(data=[go.Pie(
            labels=["Matched Skills", "Missing Skills"],
            values=[len(matched), len(missing)],
            hole=0.5
        )])

        fig.update_layout(title="Skill Analysis")
        st.plotly_chart(fig, use_container_width=True)

        # Skills Section
        col5, col6 = st.columns(2)

        with col5:
            st.subheader("✅ Matched Skills")
            for skill in matched:
                st.success(skill)

        with col6:
            st.subheader("❌ Missing Skills")
            for skill in missing:
                st.error(skill)

        # Suggestions
        st.subheader("💡 Suggestions")

        if missing:
            st.info("Learn these skills to improve your ATS score:")
            for skill in missing:
                st.write("➡️", skill)
        else:
            st.success("Perfect Resume for this role!")

else:
    st.info("Please upload a resume file to begin.")