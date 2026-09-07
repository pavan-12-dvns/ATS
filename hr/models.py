import sqlite3
from auth.models import get_db


def get_statistics():
    conn = get_db()

    total_jobs = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE is_closed = 0"
    ).fetchone()[0]

    total_applications = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    under_review = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Under Review'"
    ).fetchone()[0]

    shortlisted = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Shortlisted'"
    ).fetchone()[0]

    rejected = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Rejected'"
    ).fetchone()[0]

    conn.close()

    return {
        "total_jobs": total_jobs,
        "total": total_applications,
        "under_review": under_review,
        "shortlisted": shortlisted,
        "rejected": rejected
    }


def create_job(
    title,
    mandatory_skills,
    optional_skills,
    min_experience,
    required_education,
    weight_skills,
    weight_experience,
    weight_education,
    created_by
):
    conn = get_db()
    conn.execute("""
        INSERT INTO jobs (
            title,
            mandatory_skills,
            optional_skills,
            min_experience,
            required_education,
            skill_weight,
            experience_weight,
            education_weight,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        mandatory_skills,
        optional_skills,
        min_experience,
        required_education,
        weight_skills,
        weight_experience,
        weight_education,
        created_by
    ))
    conn.commit()
    conn.close()


def get_all_applications(job_filter=None, status_filter=None):
    conn = get_db()

    query = """
        SELECT
            a.id,
            a.candidate_id,
            a.job_id,
            a.parsed_name,
            a.parsed_email,
            a.parsed_phone,
            a.parsed_skills,
            a.parsed_experience,
            a.parsed_education,
            a.skill_score,
            a.experience_score,
            a.education_score,
            a.weighted_total,
            a.status,
            a.rejection_reason,
            a.matched_skills,
            a.missing_skills,
            a.partial_matches,
            a.score_explanation,
            a.feedback,
            a.applied_at,
            COALESCE(u.name, 'Unknown') AS candidate_name,
            COALESCE(j.title, 'Unknown Job') AS job_title
        FROM applications a
        LEFT JOIN users u ON a.candidate_id = u.id
        LEFT JOIN jobs j ON a.job_id = j.id
    """
    params = []
    conditions = []

    if job_filter:
        conditions.append("a.job_id = ?")
        params.append(job_filter)
    if status_filter:
        conditions.append("a.status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY a.applied_at DESC"

    apps = conn.execute(query, params).fetchall()
    conn.close()
    return apps


def get_application_detail(app_id):
    conn = get_db()
    app = conn.execute("""
        SELECT
            a.*,
            COALESCE(u.name, 'Unknown') AS candidate_name,
            COALESCE(u.email, '') AS candidate_email,
            COALESCE(j.title, 'Unknown Job') AS job_title
        FROM applications a
        LEFT JOIN users u ON a.candidate_id = u.id
        LEFT JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ?
    """, (app_id,)).fetchone()
    conn.close()
    return app


def update_application_status(app_id, status, feedback, user_id, ip):
    conn = get_db()
    conn.execute('''
        UPDATE applications SET status = ?, feedback = ? WHERE id = ?
    ''', (status, feedback, app_id))

    conn.execute('''
        INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, f'Status changed to {status}', 'application', app_id, feedback, ip))

    conn.commit()
    conn.close()


def get_all_jobs(include_closed=True):
    """HR always sees all jobs (open and closed) by default."""
    conn = get_db()
    cur = conn.cursor()

    if include_closed:
        cur.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    else:
        cur.execute("SELECT * FROM jobs WHERE is_closed = 0 ORDER BY created_at DESC")

    jobs = cur.fetchall()
    conn.close()
    return jobs


def delete_job(job_id):
    conn = get_db()
    app_count = conn.execute(
        "SELECT COUNT(*) as count FROM applications WHERE job_id = ?", (job_id,)
    ).fetchone()['count']

    if app_count > 0:
        conn.execute("UPDATE jobs SET is_closed = 1 WHERE id=?", (job_id,))
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()
        conn.close()
        return True


def get_job_templates():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM job_templates")
    templates = cur.fetchall()
    conn.close()
    return templates


def get_job_template_by_id(template_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, mandatory_skills, min_experience,
               required_education, weight_skills,
               weight_experience, weight_education
        FROM job_templates
        WHERE id = ?
    """, (template_id,))
    template = cur.fetchone()
    conn.close()
    return template


def update_job(job_id, data):
    conn = get_db()
    conn.execute("""
        UPDATE jobs
        SET title = ?,
            mandatory_skills = ?,
            optional_skills = ?,
            min_experience = ?,
            required_education = ?
        WHERE id = ?
    """, (
        data["title"],
        data["mandatory_skills"],
        data.get("optional_skills", ""),
        data["min_experience"],
        data["required_education"],
        job_id
    ))
    conn.commit()
    conn.close()


def get_all_skills():
    conn = get_db()
    rows = conn.execute(
        "SELECT name FROM skills ORDER BY name"
    ).fetchall()
    conn.close()
    return [row["name"] for row in rows]


def close_job(job_id):
    conn = get_db()
    conn.execute("UPDATE jobs SET is_closed = 1 WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def get_job_by_id(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return job
