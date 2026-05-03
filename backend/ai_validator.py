# backend/ai_validator.py

import os
import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def clean_json_response(text):
    text = text.strip()
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    start = text.find("{")
    end = text.rfind("}") + 1

    if start != -1 and end != -1:
        text = text[start:end]

    return text


def validate_resume(resume_text):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are a strict resume validator.

Return ONLY JSON:

{{
"is_resume": true/false,
"candidate_name": "...",
"experience_level": "...",
"confidence": number,
"summary": "...",
"reason": "..."
}}

Text:
{resume_text[:6000]}
"""
        )

        raw_text = response.text
        cleaned = clean_json_response(raw_text)
        data = json.loads(cleaned)

        return {
            "is_resume": data.get("is_resume"),
            "candidate_name": data.get("candidate_name", "Unknown"),
            "experience_level": data.get("experience_level", "Unknown"),
            "confidence": data.get("confidence", 0),
            "summary": data.get("summary", ""),
            "reason": data.get("reason", "")
        }

    except Exception as e:
        return {
            "is_resume": None,
            "candidate_name": "Unknown",
            "experience_level": "Unknown",
            "confidence": 0,
            "summary": "Gemini failed",
            "reason": str(e)
        }
