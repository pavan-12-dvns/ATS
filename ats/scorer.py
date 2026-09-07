"""
ATS Scoring Engine — TalentTrack ATS

Rules:
  - Skill score  : % of mandatory skills matched (after normalization)
  - Experience   : tiered ratio of found / required years
  - Education    : level-rank comparison
  - Weighted total from job-defined weights

Senior Safety Rule:
  If candidate experience >= job minimum AND at least one core skill matches,
  the candidate is NEVER auto-rejected regardless of total score.
  This prevents unjust rejection of experienced engineers who lack minor skills.

Inference Rule:
  Framework skills imply the parent language:
    Flask / Django => Python
    Spring / Express => matched if Java / Node.js found
    React / Angular / Vue => matched if JavaScript found
  This prevents penalising senior devs who list frameworks but not the base language.
"""

from ats.skill_normalizer import normalize_skill

AUTO_REJECT_THRESHOLD = 60

# Skills that trigger senior safety if the candidate has experience + ≥1 match
CORE_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go",
    "ruby", "php", "swift", "kotlin", "rust", "scala",
    "node.js", "react", "angular", "vue", "spring", "django", "flask",
    "fastapi", "express", "asp.net",
    "sql", "mysql", "postgresql", "mongodb",
    "aws", "azure", "gcp", "docker", "kubernetes",
}

# Inference: if candidate has KEY, it counts as having all VALUES
SKILL_INFERENCE = {
    "flask":      ["python"],
    "django":     ["python"],
    "fastapi":    ["python"],
    "spring":     ["java"],
    "express":    ["node.js", "javascript"],
    "node.js":    ["javascript"],
    "react":      ["javascript"],
    "angular":    ["javascript", "typescript"],
    "vue":        ["javascript"],
    "next.js":    ["javascript", "react"],
    "asp.net":    ["c#"],
    "rails":      ["ruby"],
    "laravel":    ["php"],
}

# ── Education ────────────────────────────────────────────────
EDU_RANK = {
    "phd": 4, "doctorate": 4,
    "master": 3, "mba": 3,
    "bachelor": 2,
    "associate": 1,
}


def education_score(candidate_list: list, required_str: str) -> float:
    if not required_str or not required_str.strip():
        return 50.0
    required_levels = [r.strip().lower() for r in required_str.split(",") if r.strip()]
    if not required_levels:
        return 50.0
    r_min = min((EDU_RANK.get(lvl, 0) for lvl in required_levels), default=0)
    if r_min == 0:
        return 50.0
    c = max((EDU_RANK.get(e.lower().strip(), 0) for e in candidate_list), default=0)
    if c >= r_min:
        return 100.0
    elif c > 0:
        return 60.0
    return 20.0


# ── Experience ───────────────────────────────────────────────
def experience_score(found: int, required: int) -> float:
    if required <= 0:
        return 50.0
    if found <= 0:
        return 0.0
    ratio = found / required
    if ratio >= 1.5:   return 100.0
    elif ratio >= 1.0: return 85.0
    elif ratio >= 0.8: return 65.0
    elif ratio >= 0.6: return 40.0
    else:              return 20.0


# ── Skill expansion (inference) ───────────────────────────────
def expand_candidate_skills(candidate_skills_set: set) -> set:
    """
    Apply inference rules: e.g. if candidate has 'flask', also credit 'python'.
    """
    expanded = set(candidate_skills_set)
    for skill in list(candidate_skills_set):
        inferred = SKILL_INFERENCE.get(skill, [])
        for inf in inferred:
            expanded.add(normalize_skill(inf))
    return expanded


# ── Main ─────────────────────────────────────────────────────
def calculate_scores(parsed: dict, job: dict) -> dict:
    job_skills_list = job.get("mandatory_skills", [])
    candidate_skills_raw = parsed.get("skills", [])
    skill_counts = parsed.get("skill_counts", {})

    # Normalize both sides
    job_skills_set = {normalize_skill(s) for s in job_skills_list if s.strip()}
    candidate_skills_set = {normalize_skill(s) for s in candidate_skills_raw if s.strip()}

    # Expand candidate skills via inference
    candidate_expanded = expand_candidate_skills(candidate_skills_set)

    matched = []
    missing = []
    for skill in sorted(job_skills_set):
        if skill in candidate_expanded:
            matched.append(skill)
        else:
            missing.append(skill)

    # Skill score
    skill_sc = (len(matched) / len(job_skills_set) * 100.0) if job_skills_set else 0.0

    # Confidence bonus from frequency (max +10)
    if skill_counts and matched:
        bonus = min(sum(skill_counts.get(s, 1) for s in matched) * 2.0, 10.0)
        skill_sc = min(skill_sc + bonus, 100.0)

    # Experience
    found_exp = parsed.get("experience_years", 0)
    req_exp = job.get("min_experience", 0)
    exp_sc = experience_score(found_exp, req_exp)

    # Education
    edu_sc = education_score(parsed.get("education", []), job.get("required_education", ""))

    # Weighted total
    w_sk = job.get("weight_skills", 40)
    w_ex = job.get("weight_experience", 30)
    w_ed = job.get("weight_education", 30)
    weight_sum = (w_sk + w_ex + w_ed) or 100
    total = (skill_sc * w_sk + exp_sc * w_ex + edu_sc * w_ed) / weight_sum

    # ── Senior Safety Rule ───────────────────────────────────
    # Condition: candidate meets experience requirement AND has ≥1 core skill match
    senior_override = False
    if (found_exp >= req_exp > 0) and matched:
        if set(matched) & CORE_SKILLS:
            senior_override = True
    # Also protect if ≥70% mandatory skills matched (regardless of experience)
    if job_skills_set and (len(matched) / len(job_skills_set)) >= 0.70:
        senior_override = True

    # Build explanation
    notes = []
    if missing:
        notes.append("Missing required skills: " + ", ".join(missing))
    if found_exp < req_exp:
        notes.append(f"Experience: {found_exp} yr found, {req_exp} yr required")
    if edu_sc < 100:
        notes.append("Education below stated preference")
    if senior_override and total < AUTO_REJECT_THRESHOLD:
        notes.append("Senior rule applied — moved to Under Review")

    return {
        "skill_score":           round(skill_sc, 2),
        "experience_score":      round(exp_sc, 2),
        "education_score":       round(edu_sc, 2),
        "total_score":           round(total, 2),
        "matched_skills":        matched,
        "missing_skills":        missing,
        "partial_matches":       [],
        "score_explanation":     " | ".join(notes),
        "senior_safety_override": senior_override,
    }
