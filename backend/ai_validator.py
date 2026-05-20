# backend/ai_validator.py

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

client = genai.Client(
    api_key=API_KEY
)


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
