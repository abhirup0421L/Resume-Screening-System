# backend/ai_analyzer.py

import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()


def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")


API_KEY = get_api_key()
client = genai.Client(api_key=API_KEY) if API_KEY else None


def analyze_resume_ai(resume_text, selected_role, required_skills):

    if not API_KEY or client is None:
        return None

    prompt = f"""
You are an expert ATS resume analyst and HR recruiter.

Analyze this resume for the selected job role.

Selected Job Role:
{selected_role}

Expected Skills:
{required_skills if required_skills else "Infer the required skills from the selected job role."}

Resume Text:
{resume_text[:7000]}

Return ONLY valid JSON in this exact format:

{{
  "ai_score": 75,
  "candidate_level": "Fresher / Junior / Mid / Senior",
  "role_fit": "Excellent / Good / Average / Poor",
  "matched_skills": [],
  "missing_skills": [],
  "strengths": [],
  "weaknesses": [],
  "improvement_suggestions": [],
  "short_summary": "short recruiter style analysis"
}}

Rules:
- ai_score must be 0 to 100.
- Do not only depend on exact keyword matching.
- Understand projects, education, experience and skills semantically.
- If resume is weak for this role, give lower score.
- Return JSON only.
- No markdown.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception as e:
        print("AI Resume Analysis Error:", e)
        return None