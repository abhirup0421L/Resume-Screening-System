# backend/skills.py (UPGRADED)

import re
from rapidfuzz import fuzz

MASTER_SKILLS = [
    "python", "java", "c", "c++", "c#", "kotlin",
    "html", "css", "javascript", "typescript",
    "react", "angular", "vue", "bootstrap",
    "nodejs", "express",
    "sql", "mysql", "mongodb", "oracle",
    "django", "flask", "spring", "hibernate",
    "machine learning", "deep learning",
    "data science", "tensorflow", "pytorch",
    "pandas", "numpy", "excel",
    "aws", "azure", "google cloud",
    "docker", "kubernetes", "linux",
    "firebase", "selenium",
    "manual testing", "automation",
    "figma", "adobe xd", "photoshop",
    "networking", "ethical hacking", "security",
    "problem solving", "communication",
    "database", "wireframing", "prototyping",
    "bug tracking"
]

# Skill aliases
ALIASES = {
    "js": "javascript",
    "reactjs": "react",
    "node": "nodejs",
    "ml": "machine learning",
    "dl": "deep learning",
    "gcp": "google cloud",
    "ps": "photoshop"
}


def extract_skills(text):
    text = text.lower()

    found = set()

    # direct aliases
    for alias, real in ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            found.add(real)

    # exact match
    for skill in MASTER_SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found.add(skill)

    # fuzzy token match
    words = text.split()

    for word in words:
        for skill in MASTER_SKILLS:
            if fuzz.ratio(word, skill) >= 88:
                found.add(skill)

    return list(found)