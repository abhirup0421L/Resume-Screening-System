# Upload.py

import streamlit as st
import json
from backend.parser import extract_text
from backend.skills import extract_skills
from backend.matcher import match_skills

st.title("📤 Upload Resume")

uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx", "txt"]
)

# Load all job roles dynamically
with open("data/roles.json", "r") as file:
    roles_data = json.load(file)

job_roles = list(roles_data.keys())

job_role = st.selectbox(
    "Select Job Role",
    job_roles
)

if uploaded_file is not None:

    st.success("Resume Uploaded Successfully!")

    if st.button("Analyze Resume"):

        resume_text = extract_text(uploaded_file)

        candidate_skills = extract_skills(resume_text)

        score, matched, missing = match_skills(candidate_skills, job_role)

        st.session_state.score = score
        st.session_state.matched = matched
        st.session_state.missing = missing
        st.session_state.role = job_role

        st.success("Analysis Completed!")
        st.info("Now open Result page from sidebar.")
