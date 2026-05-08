# backend/ai_validator.py

import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

# --------------------------
# Load Environment
# --------------------------
load_dotenv()


# --------------------------
# Get API Key
# --------------------------
def get_api_key():

    # Streamlit Cloud Secrets
    try:
        return st.secrets["GEMINI_API_KEY"]

    # Local .env fallback
    except Exception:
        return os.getenv("GEMINI_API_KEY")


API_KEY = get_api_key()


# --------------------------
# Gemini Client
# --------------------------
client = genai.Client(
    api_key=API_KEY
)


# --------------------------
# Resume Validation
# --------------------------
def validate_resume(resume_text):

    if not API_KEY:
        return {
            "is_resume": None,
            "candidate_name": "Unknown",
            "experience_level": "Unknown",
            "summary": "Gemini API key missing.",
            "confidence": 0,
            "reason": "API key not found."
        }

    prompt = f"""
You are an expert HR recruiter.

Analyze the given document carefully.

Return ONLY valid JSON in this exact format:

{{
  "is_resume": true,
  "candidate_name": "Name or Unknown",
  "experience_level": "Fresher / Junior / Mid / Senior / Unknown",
  "summary": "Short professional summary",
  "confidence": 90,
  "reason": "Why"
}}

Rules:
- If document is a real resume/CV → is_resume true
- If random article, notes, tutorial, copied skill list, or fake PDF → is_resume false
- Return JSON only
- No markdown
- No explanations

Document Text:
{resume_text[:6000]}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        text = response.text.strip()

        # Remove markdown formatting if exists
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        result = json.loads(text)

        return result

    except Exception as e:

        print("Gemini Validation Error:", e)

        return {
            "is_resume": None,
            "candidate_name": "Unknown",
            "experience_level": "Unknown",
            "summary": "Gemini AI unavailable.",
            "confidence": 0,
            "reason": str(e)
        }
