from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth.models import authenticate_user, create_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = authenticate_user(email, password)
        
        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            
            if user['role'] == 'hr':
                return redirect(url_for('hr.dashboard'))
            else:
                return redirect(url_for('candidate.dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        company = request.form.get('company') if role == 'hr' else None
        
        # Server-side password confirmation validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
        
        if create_user(name, email, password, role, company):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email already registered', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('landing'))
