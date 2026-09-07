"""
ATS Processing Pipeline
Orchestrates: parse → score → persist → set status
"""

from auth.models import get_db
from ats.parser import parse_resume
from ats.scorer import calculate_scores, AUTO_REJECT_THRESHOLD
from ats.skill_normalizer import normalize_skill_list


def sanitize_parsed_data(parsed: dict) -> dict | None:
    if not parsed:
        return None
    return {
        "name":             parsed.get("name", "Unknown"),
        "email":            parsed.get("email", "Not found"),
        "phone":            parsed.get("phone", "Not found"),
        "skills":           parsed.get("skills", []),
        "skill_counts":     parsed.get("skill_counts", {}),
        "experience_years": parsed.get("experience_years", 0),
        "education":        parsed.get("education", []),
    }


def safe_join(val) -> str:
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return val or ""


def process_application(app_id: int, filepath: str, filename: str):
    conn = get_db()

    # Parse
    parsed_raw = parse_resume(filepath, filename)
    parsed = sanitize_parsed_data(parsed_raw)

    print(f"[ATS] Processing app_id={app_id}, file={filename}")

    if not parsed:
        conn.execute("""
            UPDATE applications
            SET status = 'Rejected',
                rejection_reason = 'Resume could not be parsed or is empty'
            WHERE id = ?
        """, (app_id,))
        conn.commit()
        conn.close()
        return

    # Load job data
    row = conn.execute("""
        SELECT a.id, j.mandatory_skills, j.optional_skills,
               j.min_experience, j.required_education,
               j.skill_weight, j.experience_weight, j.education_weight
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ?
    """, (app_id,)).fetchone()

    if not row:
        conn.close()
        return

    mandatory_raw = row["mandatory_skills"] or ""
    mandatory_skills = normalize_skill_list(
        [s.strip() for s in mandatory_raw.split(",") if s.strip()]
    )

    job_data = {
        "mandatory_skills":  mandatory_skills,
        "min_experience":    row["min_experience"] or 0,
        "required_education": row["required_education"] or "",
        "weight_skills":     row["skill_weight"],
        "weight_experience": row["experience_weight"],
        "weight_education":  row["education_weight"],
    }

    # Score
    scores = calculate_scores(parsed, job_data)

    print(f"[ATS] Scores: total={scores['total_score']}, "
          f"skill={scores['skill_score']}, exp={scores['experience_score']}, "
          f"edu={scores['education_score']}, "
          f"senior_override={scores['senior_safety_override']}")

    # Determine status
    if scores["senior_safety_override"]:
        final_status = "Under Review"
        rejection_reason = None
    elif scores["total_score"] < AUTO_REJECT_THRESHOLD:
        final_status = "Rejected"
        parts = []
        if scores["missing_skills"]:
            parts.append("Missing required skills: " + ", ".join(scores["missing_skills"]))
        if not parts:
            parts.append("Did not meet the minimum screening threshold")
        rejection_reason = " | ".join(parts)
    else:
        final_status = "Under Review"
        rejection_reason = None

    print(f"[ATS] Final status: {final_status}")

    # Persist
    conn.execute("""
        UPDATE applications
        SET parsed_name       = ?,
            parsed_email      = ?,
            parsed_phone      = ?,
            parsed_skills     = ?,
            parsed_experience = ?,
            parsed_education  = ?,
            skill_score       = ?,
            experience_score  = ?,
            education_score   = ?,
            weighted_total    = ?,
            status            = ?,
            rejection_reason  = ?,
            matched_skills    = ?,
            missing_skills    = ?,
            partial_matches   = ?,
            score_explanation = ?
        WHERE id = ?
    """, (
        parsed["name"],
        parsed["email"],
        parsed["phone"],
        safe_join(parsed["skills"]),
        parsed["experience_years"],
        safe_join(parsed["education"]),
        scores["skill_score"],
        scores["experience_score"],
        scores["education_score"],
        scores["total_score"],
        final_status,
        rejection_reason,
        safe_join(scores["matched_skills"]),
        safe_join(scores["missing_skills"]),
        safe_join(scores["partial_matches"]),
        scores["score_explanation"],
        app_id,
    ))

    conn.commit()
    conn.close()
