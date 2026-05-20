# backend/skills.py

import re
from rapidfuzz import fuzz

MASTER_SKILLS = [
    # Programming / IT
    "python", "java", "c", "c++", "c#", "kotlin",
    "html", "css", "javascript", "typescript",
    "react", "angular", "vue", "bootstrap",
    "nodejs", "express", "django", "flask",
    "spring", "spring boot", "hibernate",
    "sql", "mysql", "mongodb", "oracle", "database",
    "machine learning", "deep learning", "data science",
    "tensorflow", "pytorch", "pandas", "numpy",
    "aws", "azure", "google cloud", "docker", "kubernetes",
    "linux", "firebase", "selenium", "manual testing",
    "automation", "bug tracking", "networking",
    "ethical hacking", "security", "cyber security",

    # Design / UI UX
    "figma", "adobe xd", "photoshop", "illustrator",
    "canva", "wireframing", "prototyping", "branding",

    # Core Engineering
    "autocad", "solidworks", "catia", "manufacturing",
    "thermodynamics", "cad", "staad pro", "surveying",
    "construction", "estimation", "circuit design",
    "power systems", "electrical machines", "matlab",
    "autocad electrical", "embedded systems", "arduino",
    "vlsi", "pcb design", "microcontrollers",

    # Business / Management
    "communication", "problem solving", "leadership",
    "teamwork", "recruitment", "payroll",
    "employee relations", "hrms", "sales",
    "negotiation", "crm", "marketing",
    "customer service", "email support",
    "data analysis", "power bi", "business analysis",

    # Digital Marketing / Content
    "seo", "google ads", "social media marketing",
    "content marketing", "analytics", "content writing",
    "blogging", "copywriting", "editing",

    # Finance / Accounting
    "financial analysis", "accounting", "budgeting",
    "forecasting", "tally", "gst", "taxation",

    # Education / Healthcare
    "teaching", "lesson planning", "subject knowledge",
    "classroom management", "patient care",
    "medical assistance", "healthcare", "vital signs",
    "pharmacy", "medicines", "patient counseling",
    "inventory", "medical knowledge"
]

ALIASES = {
    "js": "javascript",
    "reactjs": "react",
    "node": "nodejs",
    "node js": "nodejs",
    "ml": "machine learning",
    "dl": "deep learning",
    "gcp": "google cloud",
    "ps": "photoshop",
    "ai": "artificial intelligence",
    "autocad electrical": "autocad electrical",
    "staad": "staad pro",
    "ms excel": "excel",
    "powerbi": "power bi",
    "smm": "social media marketing",
    "hr": "recruitment",
    "customer support": "customer service"
}


def extract_skills(text):
    if not text:
        return []

    text = text.lower()
    found = set()

    # Alias matching
    for alias, real in ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            found.add(real)

    # Exact skill phrase matching
    for skill in MASTER_SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found.add(skill)

    # Fuzzy matching for single-word skills only
    words = re.findall(r"\b[a-zA-Z0-9+#.]+\b", text)

    single_word_skills = [
        skill for skill in MASTER_SKILLS
        if len(skill.split()) == 1
    ]

    for word in words:
        for skill in single_word_skills:
            if fuzz.ratio(word, skill) >= 90:
                found.add(skill)

    return sorted(list(found))
