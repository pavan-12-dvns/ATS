import sqlite3
import hashlib
from functools import wraps
from flask import session, redirect, url_for, flash
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, '..', 'database', 'ats.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def create_user(name, email, password, role, company=None):
    conn = get_db()
    try:
        password_hash = hash_password(password)
        conn.execute(
            'INSERT INTO users (name, email, password_hash, role, company) VALUES (?, ?, ?, ?, ?)',
            (name, email, password_hash, role, company)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE email = ? AND is_active = 1',
        (email,)
    ).fetchone()
    conn.close()
    
    if user and verify_password(user['password_hash'], password):
        return dict(user)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'hr':
            flash('HR access required', 'danger')
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    return decorated_function

def candidate_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'candidate':
            flash('Candidate access required', 'danger')
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    return decorated_function
