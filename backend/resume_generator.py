# backend/resume_generator.py

import os
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
client = genai.Client(api_key=API_KEY)


def generate_resume(
    name,
    email,
    phone,
    education,
    skills,
    experience,
    projects,
    target_role
):

    if not API_KEY:
        return "Gemini API key missing."

    prompt = f"""
You are an expert resume writer and ATS optimization specialist.

Create a professional, clean, ATS-friendly resume for the target role.

IMPORTANT RULES:
- Do NOT invent fake companies, fake marks, fake years, or fake achievements.
- Improve wording professionally using only the details provided.
- If experience is "Fresher" or empty, create a strong fresher resume.
- Use clear section headings.
- Keep formatting simple and ATS readable.
- Use bullet points.
- Avoid tables, emojis, markdown symbols, and decorative characters.
- Make the resume suitable for a college student / fresher if experience is low.
- Keep it concise, professional, and recruiter-friendly.

CANDIDATE DETAILS:
Name: {name}
Email: {email}
Phone: {phone}
Target Role: {target_role}

Education:
{education}

Skills:
{skills}

Experience:
{experience}

Projects:
{projects}

OUTPUT FORMAT EXACTLY LIKE THIS:

{name.upper()}
Email: {email} | Phone: {phone}
Target Role: {target_role}

PROFESSIONAL SUMMARY
Write 3-4 strong lines based on the candidate details.

TECHNICAL SKILLS
- Programming Languages:
- Web/Frameworks:
- Databases:
- Tools/Platforms:
- Other Skills:

EDUCATION
Rewrite education professionally.

PROJECTS
For each project, write:
Project Name
- What the project does
- Technologies used
- Impact or outcome

EXPERIENCE
If experience is available, rewrite professionally.
If fresher, write:
Fresher with hands-on academic and project experience.

CERTIFICATIONS
Write "Available upon request" if not provided.

STRENGTHS
- Problem solving
- Quick learning
- Team collaboration
- Communication

ATS KEYWORDS
Add relevant keywords for {target_role}.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        return f"""
Gemini AI is currently unavailable.

Reason:
{str(e)}
"""