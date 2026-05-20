# backend/interview.py

import json
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from google import genai

from backend.database import interview_progress_collection
from backend.credits import get_credits, deduct_credit

load_dotenv()


def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY")


API_KEY = get_api_key()
client = genai.Client(api_key=API_KEY) if API_KEY else None


INTERVIEW_LEVEL_COST = 50

LEVEL_DETAILS = {
    1: {"difficulty": "Easy", "questions": 5, "time": 300},
    2: {"difficulty": "Basic", "questions": 5, "time": 420},
    3: {"difficulty": "Intermediate", "questions": 7, "time": 600},
    4: {"difficulty": "Advanced", "questions": 8, "time": 720},
    5: {"difficulty": "Real Interview Level", "questions": 10, "time": 900}
}


def get_user_progress(email, role):
    email = email.strip().lower()

    progress = interview_progress_collection.find_one({
        "email": email,
        "role": role
    })

    if not progress:
        progress = {
            "email": email,
            "role": role,
            "unlocked_level": 1,
            "stars": 0,
            "best_score": 0,
            "completed_levels": [],
            "updated_at": datetime.utcnow()
        }

        interview_progress_collection.insert_one(progress)

    return progress


def generate_interview_questions(email, role, level):
    if not API_KEY or client is None:
        return False, "Gemini API key missing.", []

    level = int(level)
    details = LEVEL_DETAILS[level]

    credits = get_credits(email)

    if credits < INTERVIEW_LEVEL_COST:
        return False, "Not enough credits.", []

    prompt = f"""
Generate {details["questions"]} unique MCQ interview questions.

Job Role: {role}
Level: {level}
Difficulty: {details["difficulty"]}

Rules:
- Every question must be unique.
- Questions should become harder in higher levels.
- Each question must have exactly 4 options.
- Only one correct answer.
- Return JSON only.
- No markdown.
- No explanation outside JSON.

JSON FORMAT:
[
  {{
    "question": "question text",
    "options": [
        "option 1",
        "option 2",
        "option 3",
        "option 4"
    ],
    "correct_answer": "exact correct option",
    "explanation": "short explanation"
  }}
]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        questions = json.loads(text)

        deduct_credit(email, INTERVIEW_LEVEL_COST)

        return True, "Questions generated successfully.", questions

    except Exception as e:
        print("Interview Generation Error:", e)
        return False, "Generation failed. Try again later.", []


def check_answers(questions, user_answers):
    correct = 0
    results = []

    for i, q in enumerate(questions):
        user_answer = user_answers.get(str(i), "")
        correct_answer = q.get("correct_answer", "")
        is_correct = user_answer == correct_answer

        if is_correct:
            correct += 1

        results.append({
            "question": q.get("question", ""),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })

    score = int((correct / len(questions)) * 100) if questions else 0

    return score, results


def calculate_stars(score):
    if score >= 80:
        return 3
    elif score >= 60:
        return 2
    elif score >= 40:
        return 1

    return 0


def update_user_progress(email, role, level, score):
    email = email.strip().lower()
    level = int(level)

    stars = calculate_stars(score)
    progress = get_user_progress(email, role)

    unlocked_level = progress.get("unlocked_level", 1)
    completed_levels = progress.get("completed_levels", [])
    total_stars = progress.get("stars", 0)
    best_score = progress.get("best_score", 0)

    if score >= 60:
        if level not in completed_levels:
            completed_levels.append(level)
            total_stars += stars

        if level == unlocked_level and unlocked_level < 5:
            unlocked_level += 1

    if score > best_score:
        best_score = score

    interview_progress_collection.update_one(
        {
            "email": email,
            "role": role
        },
        {
            "$set": {
                "unlocked_level": unlocked_level,
                "stars": total_stars,
                "best_score": best_score,
                "completed_levels": completed_levels,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    return stars, unlocked_level
