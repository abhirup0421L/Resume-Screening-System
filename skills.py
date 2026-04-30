# skills.py

import re

def extract_skills(text):

    skills_list = [
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
        "firebase",
        "selenium", "manual testing", "automation",
        "figma", "adobe xd", "photoshop",
        "networking", "ethical hacking", "security",
        "problem solving", "communication",
        "database", "wireframing", "prototyping",
        "bug tracking"
    ]

    text = text.lower()
    found_skills = []

    for skill in skills_list:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found_skills.append(skill)

    return found_skills