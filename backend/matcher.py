# matcher.py

import json

def load_roles():
    with open("data/roles.json", "r") as file:
        return json.load(file)


def match_skills(candidate_skills, job_role):

    roles = load_roles()

    required_skills = roles.get(job_role, [])

    matched = []
    missing = []

    for skill in required_skills:
        if skill in candidate_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    if len(required_skills) > 0:
        score = int((len(matched) / len(required_skills)) * 100)
    else:
        score = 0

    return score, matched, missing
