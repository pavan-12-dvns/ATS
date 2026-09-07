from auth.models import get_db


def get_candidate_applications(user_id: int) -> list:
    conn = get_db()
    apps = conn.execute("""
        SELECT
            a.*,
            COALESCE(j.title, 'Position Unavailable') AS job_title
        FROM applications a
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE a.candidate_id = ?
        ORDER BY a.applied_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return apps


def get_available_jobs() -> list:
    conn = get_db()
    jobs = conn.execute("""
        SELECT
            j.id,
            j.title,
            j.mandatory_skills,
            j.optional_skills,
            j.min_experience,
            j.required_education,
            COALESCE(u.company, 'Company') AS company_name
        FROM jobs j
        LEFT JOIN users u ON j.created_by = u.id
        WHERE j.is_closed = 0
        ORDER BY j.created_at DESC
    """).fetchall()
    conn.close()
    return jobs


def check_existing_application(candidate_id: int, job_id) -> bool:
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM applications WHERE candidate_id = ? AND job_id = ?",
        (candidate_id, int(job_id))
    ).fetchone()
    conn.close()
    return existing is not None


def create_application(candidate_id: int, job_id, resume_path: str, resume_hash: str, file_size: int) -> int:
    conn = get_db()
    conn.execute(
        "INSERT INTO applications (candidate_id, job_id, resume_path, resume_hash) VALUES (?, ?, ?, ?)",
        (candidate_id, int(job_id), resume_path, resume_hash)
    )
    app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return app_id
