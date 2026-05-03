# backend/matcher.py

def match_skills(user_skills, required_skills):
    """
    Compare extracted skills with required job skills

    Args:
        user_skills (list): skills from resume
        required_skills (list): skills from selected job role

    Returns:
        score (int): match percentage
        matched (list): matched skills
        missing (list): missing skills
    """

    # Safety check
    if not isinstance(user_skills, list):
        user_skills = []

    if not isinstance(required_skills, list):
        required_skills = []

    # Normalize
    user_skills = [skill.lower().strip() for skill in user_skills]
    required_skills = [skill.lower().strip() for skill in required_skills]

    matched = []
    missing = []

    for skill in required_skills:
        if skill in user_skills:
            matched.append(skill)
        else:
            missing.append(skill)

    # Score calculation
    if len(required_skills) == 0:
        score = 0
    else:
        score = round((len(matched) / len(required_skills)) * 100)

    return score, matched, missing
