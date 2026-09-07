from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from auth.models import candidate_required, get_db
from candidate.models import *
from ats.pipeline import process_application
import os
import hashlib

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidate')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    apps = get_candidate_applications(session['user_id'])
    jobs = get_available_jobs()
    return render_template('candidate/dashboard.html', apps=apps, jobs=jobs)

@candidate_bp.route('/upload', methods=['GET', 'POST'])
@candidate_required
def upload():
    if request.method == 'POST':
        job_id = request.form.get('job_id')
        file = request.files.get('resume')
        
        if not job_id or not file or file.filename == '':
            flash('Please select job and resume', 'danger')
            return redirect(url_for('candidate.upload'))
        
        if not allowed_file(file.filename):
            flash('Only PDF and DOCX files allowed', 'danger')
            return redirect(url_for('candidate.upload'))
        
        if check_existing_application(session['user_id'], job_id):
            flash('You already applied to this job', 'warning')
            return redirect(url_for('candidate.dashboard'))
        
        # Backend enforcement: reject applications to closed jobs
        conn = get_db()
        job = conn.execute('SELECT is_closed FROM jobs WHERE id = ?', (job_id,)).fetchone()
        conn.close()
        if not job or job['is_closed']:
            flash('This job is no longer accepting applications', 'danger')
            return redirect(url_for('candidate.dashboard'))
        
        filename = secure_filename(f"{session['user_id']}_{job_id}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            os.remove(filepath)
            flash('File too large (max 5MB)', 'danger')
            return redirect(url_for('candidate.upload'))
        
        resume_hash = calculate_hash(filepath)
        app_id = create_application(session['user_id'], job_id, filepath, resume_hash, file_size)
        
        process_application(app_id, filepath, file.filename)
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('candidate.status'))
    
    jobs = get_available_jobs()
    return render_template('candidate/upload.html', jobs=jobs)

@candidate_bp.route('/status')
@candidate_required
def status():
    apps = get_candidate_applications(session['user_id'])
    return render_template('candidate/status.html', apps=apps)
