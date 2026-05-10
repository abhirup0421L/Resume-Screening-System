import json
from datetime import datetime
from google import genai
import os
from dotenv import load_dotenv

from backend.database import interview_progress_collection
from backend.credits import get_credits, deduct_credit

load_dotenv()



client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# =====================================================
# SETTINGS
# =====================================================

INTERVIEW_LEVEL_COST = 50

LEVEL_DETAILS = {
    1: {
        "difficulty": "Easy",
        "questions": 5,
        "time": 300
    },

    2: {
        "difficulty": "Basic",
        "questions": 5,
        "time": 420
    },

    3: {
        "difficulty": "Intermediate",
        "questions": 7,
        "time": 600
    },

    4: {
        "difficulty": "Advanced",
        "questions": 8,
        "time": 720
    },

    5: {
        "difficulty": "Real Interview Level",
        "questions": 10,
        "time": 900
    }
}


# =====================================================
# USER PROGRESS
# =====================================================

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


# =====================================================
# GENERATE QUESTIONS
# =====================================================

def generate_interview_questions(email, role, level):

    level = int(level)

    details = LEVEL_DETAILS[level]

    # CHECK CREDITS
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

        # DEDUCT CREDITS ONLY AFTER SUCCESS
        deduct_credit(email, INTERVIEW_LEVEL_COST)

        return True, "Questions generated successfully.", questions

    except Exception:

        return False, "Generation failed. Try again later.", []


# =====================================================
# CHECK ANSWERS
# =====================================================

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

    score = int(
        (correct / len(questions)) * 100
    ) if questions else 0

    return score, results


# =====================================================
# STAR SYSTEM
# =====================================================

def calculate_stars(score):

    if score >= 80:
        return 3

    elif score >= 60:
        return 2

    elif score >= 40:
        return 1

    return 0


# =====================================================
# UPDATE PROGRESS
# =====================================================

def update_user_progress(email, role, level, score):

    email = email.strip().lower()

    level = int(level)

    stars = calculate_stars(score)

    progress = get_user_progress(email, role)

    unlocked_level = progress.get(
        "unlocked_level",
        1
    )

    completed_levels = progress.get(
        "completed_levels",
        []
    )

    total_stars = progress.get(
        "stars",
        0
    )

    best_score = progress.get(
        "best_score",
        0
    )

    # PASS CONDITION
    if score >= 60:

        if level not in completed_levels:

            completed_levels.append(level)

            total_stars += stars

        if (
            level == unlocked_level
            and unlocked_level < 5
        ):
            unlocked_level += 1

    # BEST SCORE
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