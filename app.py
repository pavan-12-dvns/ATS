import os
import sqlite3
from flask import Flask, render_template
from auth.routes import auth_bp
from hr.routes import hr_bp
from candidate.routes import candidate_bp

# ------------------ APP SETUP ------------------
app = Flask(__name__)
app.secret_key = 'change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

# ------------------ DATABASE ------------------
DB_PATH = os.path.join('database', 'ats.db')

def init_db():
    os.makedirs('database', exist_ok=True)
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open('database/schema.sql', 'r') as f:
            conn.executescript(f.read())

        import hashlib
        hr_pass = hashlib.sha256('hr123'.encode()).hexdigest()
        cand_pass = hashlib.sha256('john123'.encode()).hexdigest()

        conn.execute(
            'INSERT INTO users (name, email, password_hash, role, company) VALUES (?, ?, ?, ?, ?)',
            ('HR Manager', 'hr@company.com', hr_pass, 'hr', 'TechCorp')
        )
        conn.execute(
            'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
            ('John Doe', 'john@email.com', cand_pass, 'candidate')
        )

        conn.execute('''
            INSERT INTO jobs (title, mandatory_skills, optional_skills, min_experience,
                              required_education, skill_weight, experience_weight, education_weight, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Senior Software Engineer', 'javascript,react,python', 'node.js,typescript,aws',
              3, 'Bachelor,Master,PhD', 40, 30, 30, 1))

        conn.commit()
        conn.close()
    else:
        # Sync skills catalog into existing DB (INSERT OR IGNORE is safe to re-run)
        _sync_skills()


def _sync_skills():
    """Ensure all catalog skills exist in the skills table."""
    from ats.skill_normalizer import SKILL_ALIASES
    conn = sqlite3.connect(DB_PATH)
    for canonical in SKILL_ALIASES.keys():
        conn.execute('INSERT OR IGNORE INTO skills (name) VALUES (?)', (canonical.lower().strip(),))
    conn.commit()
    conn.close()


# ------------------ BLUEPRINTS ------------------
app.register_blueprint(auth_bp)
app.register_blueprint(hr_bp)
app.register_blueprint(candidate_bp)

# ------------------ LANDING PAGE ------------------
@app.route('/')
def landing():
    return render_template('landing.html')

# ------------------ UPLOAD FOLDER ------------------
os.makedirs('uploads', exist_ok=True)

# ------------------ RUN ------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
