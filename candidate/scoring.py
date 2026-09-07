# candidate/scoring.py

import re
from auth.models import get_db


# -------------------------
# A. BASIC NORMALIZATION
# -------------------------
def normalize_skill(skill: str) -> str:
    """
    Normalize skill text only (NO synonyms here)
    """
    return skill.strip().lower()


# -------------------------
# B. TOKENIZE SKILLS
# -------------------------
def extract_skills_from_text(text: str) -> list[str]:
    """
    Very basic extractor.
    Later you can replace with NLP.
    """
    if not text:
        return []

    # split by commas, slashes, newlines
    raw_skills = re.split(r"[,\n/]+", text)
    return [normalize_skill(s) for s in raw_skills if s.strip()]


# -------------------------
# C. SYNONYM RESOLUTION (DB-DRIVEN)
# -------------------------
def resolve_synonyms(skills: list[str]) -> list[str]:
    """
    Maps skill variants to canonical skill names using DB.
    """
    if not skills:
        return []

    conn = get_db()

    resolved = []

    for skill in skills:
        row = conn.execute(
            """
            SELECT canonical_skill
            FROM skill_synonyms
            WHERE variant = ?
            """,
            (skill,)
        ).fetchone()

        if row:
            resolved.append(row["canonical_skill"])
        else:
            resolved.append(skill)

    conn.close()

    # remove duplicates automatically
    return list(set(resolved))


# -------------------------
# D. MANDATORY SKILL CHECK
# -------------------------
def mandatory_skills_present(job_skills: list[str], candidate_skills: list[str]) -> bool:
    """
    ALL mandatory skills must exist.
    """
    return all(skill in candidate_skills for skill in job_skills)


# -------------------------
# E. FINAL ATS SCORING
# -------------------------
def score_application(job: dict, resume_text: str) -> dict:
    """
    Returns:
    {
        total_score,
        skill_score,
        experience_score,
        education_score,
        auto_rejected
    }
    """

    # --- job data ---
    mandatory_skills = extract_skills_from_text(job["mandatory_skills"])
    optional_skills = extract_skills_from_text(job.get("optional_skills", ""))

    mandatory_skills = resolve_synonyms(mandatory_skills)
    optional_skills = resolve_synonyms(optional_skills)

    # --- resume skills ---
    resume_skills = extract_skills_from_text(resume_text)
    resume_skills = resolve_synonyms(resume_skills)

    # --- mandatory check ---
    if not mandatory_skills_present(mandatory_skills, resume_skills):
        return {
            "total_score": 0,
            "skill_score": 0,
            "experience_score": 0,
            "education_score": 0,
            "auto_rejected": True
        }

    # --- skill score ---
    matched_mandatory = len(set(mandatory_skills) & set(resume_skills))
    matched_optional = len(set(optional_skills) & set(resume_skills))

    skill_ratio = (
        matched_mandatory + (0.5 * matched_optional)
    ) / max(len(mandatory_skills), 1)

    skill_score = skill_ratio * job["weight_skills"]

    # --- experience score (simple) ---
    experience_score = job["weight_experience"]  # placeholder (you already handle exp elsewhere)

    # --- education score (simple) ---
    education_score = job["weight_education"]  # placeholder

    total_score = round(skill_score + experience_score + education_score, 2)

    return {
        "total_score": total_score,
        "skill_score": round(skill_score, 2),
        "experience_score": experience_score,
        "education_score": education_score,
        "auto_rejected": False
    }
