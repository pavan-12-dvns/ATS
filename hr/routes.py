from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth.models import hr_required
from hr.models import (
    create_job, get_job_templates, get_job_template_by_id, get_all_skills,
    get_statistics, get_all_applications, get_application_detail,
    update_application_status, get_all_jobs, delete_job, close_job,
    update_job, get_job_by_id
)

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


@hr_bp.route('/dashboard')
@hr_required
def dashboard():
    stats  = get_statistics()
    recent = get_all_applications()[:5]
    return render_template("hr/dashboard.html", stats=stats, recent=recent)


@hr_bp.route('/create-job', methods=['GET', 'POST'])
@hr_required
def create_job_route():
    templates = get_job_templates()
    skills    = get_all_skills()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()

        # Mandatory skills: text field takes priority; fallback to checkboxes
        # The form sends either a free-text "mandatory_skills" field
        # OR multiple checkbox values with the same name.
        raw_mandatory = request.form.get('mandatory_skills', '').strip()
        if not raw_mandatory:
            # Checkboxes — getlist returns individual values
            raw_mandatory = ",".join(request.form.getlist('mandatory_skills'))

        optional_skills = request.form.get('optional_skills', '').strip()
        min_exp = int(request.form.get('min_experience', 0) or 0)
        edu     = request.form.get('required_education', '').strip()

        try:
            skill_w = int(request.form.get('skill_weight', 0))
            exp_w   = int(request.form.get('experience_weight', 0))
            edu_w   = int(request.form.get('education_weight', 0))
        except (ValueError, TypeError):
            flash('Invalid weight values', 'danger')
            return redirect(url_for('hr.create_job_route'))

        if skill_w + exp_w + edu_w != 100:
            flash('Weights must sum to exactly 100%', 'danger')
            return redirect(url_for('hr.create_job_route'))

        if not title or not raw_mandatory:
            flash('Job title and mandatory skills are required', 'danger')
            return redirect(url_for('hr.create_job_route'))

        create_job(title, raw_mandatory, optional_skills, min_exp,
                   edu, skill_w, exp_w, edu_w, session['user_id'])
        flash('Job created successfully!', 'success')
        return redirect(url_for('hr.dashboard'))

    return render_template('hr/create_job.html', templates=templates, skills=skills)


@hr_bp.route('/candidate/<int:id>')
@hr_required
def candidate_detail(id):
    app = get_application_detail(id)
    if not app:
        flash('Application not found', 'danger')
        return redirect(url_for('hr.candidates'))
    return render_template('hr/candidate_detail.html', app=app)


@hr_bp.route('/candidate/<int:id>/update', methods=['POST'])
@hr_required
def update_status(id):
    app = get_application_detail(id)
    if not app:
        flash('Application not found', 'danger')
        return redirect(url_for('hr.candidates'))
    status   = request.form.get('status', '').strip()
    feedback = request.form.get('feedback', '').strip()
    valid_statuses = {'Under Review', 'Shortlisted', 'Interview', 'Rejected'}
    if status not in valid_statuses:
        flash('Invalid status value', 'danger')
        return redirect(url_for('hr.candidate_detail', id=id))
    update_application_status(id, status, feedback, session['user_id'], request.remote_addr)
    flash(f'Status updated to {status}', 'success')
    return redirect(url_for('hr.candidate_detail', id=id))


@hr_bp.route('/candidates')
@hr_required
def candidates():
    job_filter    = request.args.get('job', '').strip()
    status_filter = request.args.get('status', '').strip()
    all_apps  = get_all_applications(
        job_filter    = job_filter    or None,
        status_filter = status_filter or None,
    )
    all_jobs = get_all_jobs(include_closed=True)
    return render_template(
        'hr/candidates.html',
        apps=all_apps,
        jobs=all_jobs,
        job_filter=job_filter,
        status_filter=status_filter,
    )


@hr_bp.route('/settings')
@hr_required
def settings():
    return render_template('hr/settings.html')


@hr_bp.route('/job-templates')
@hr_required
def job_templates():
    templates = get_job_templates()
    return {"templates": [dict(t) for t in templates]}


@hr_bp.route('/job-templates/<int:template_id>')
@hr_required
def job_template_detail(template_id):
    t = get_job_template_by_id(template_id)
    if not t:
        return {"error": "not found"}, 404
    return {
        "title":             t["title"],
        "mandatory_skills":  t["mandatory_skills"],
        "min_experience":    t["min_experience"],
        "required_education":t["required_education"],
        "weight_skills":     t["weight_skills"],
        "weight_experience": t["weight_experience"],
        "weight_education":  t["weight_education"],
    }


@hr_bp.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
@hr_required
def edit_job(job_id):
    job = get_job_by_id(job_id)
    if not job:
        flash("Job not found", "danger")
        return redirect(url_for('hr.view_jobs'))
    if request.method == 'POST':
        update_job(job_id, request.form)
        flash("Job updated. Scoring weights remain locked.", "success")
        return redirect(url_for('hr.view_jobs'))
    return render_template('hr/edit_job.html', job=job)


@hr_bp.route('/jobs')
@hr_required
def view_jobs():
    jobs = get_all_jobs(include_closed=True)
    return render_template("hr/jobs.html", jobs=jobs)


@hr_bp.route('/jobs/<int:job_id>/delete', methods=["POST"])
@hr_required
def remove_job(job_id):
    was_deleted = delete_job(job_id)
    if was_deleted:
        flash("Job deleted successfully.", "success")
    else:
        flash("Job has existing applications — it has been closed instead of deleted.", "warning")
    return redirect(url_for("hr.view_jobs"))


@hr_bp.route('/jobs/<int:job_id>/close', methods=["POST"])
@hr_required
def close_job_route(job_id):
    close_job(job_id)
    flash("Job closed. Existing applications are preserved.", "success")
    return redirect(url_for("hr.view_jobs"))
