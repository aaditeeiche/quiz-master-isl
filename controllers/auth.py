from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import text
from models.models import db, Admin, User, Feedback
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime

auth_bp = Blueprint('auth', __name__)

# Admin Login Route
@auth_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html', role='admin')

@auth_bp.route('/vulnerable_login', methods=['GET', 'POST'])
def vulnerable_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = text(f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'")
        result = db.session.execute(query).fetchone()

        if result:
            session['user_id'] = result[0]  # Assuming first column is id
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return render_template('login.html', role='vulnerable_user')

    return render_template('login.html', role='vulnerable_user')

# User Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        qualification = request.form['qualification']
        dob_str = request.form['dob']

        # Email validation regex
        import re
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, username):
            flash("Invalid email format. Please enter a valid email.", "danger")
            return redirect(url_for('auth.register'))

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('auth.register'))

        # Age validation (User should be at least 12 years old and not in the future)
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if dob > today:
            flash("Date of birth cannot be in the future.", "danger")
            return redirect(url_for('auth.register'))

        if age < 12:
            flash("You must be at least 12 years old to register.", "danger")
            return redirect(url_for('auth.register'))

        # Check if username (email) is already taken
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('auth.register'))

        # Create and save the new user
        user = User(username=username, full_name=full_name, qualification=qualification, dob=dob)
        user.set_password(password)  # Hash password
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.user_login'))
    
    return render_template('register.html')

# User Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html', role='user')

# Logout Route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Feedback Route
@auth_bp.route('/')
def index():
    feedbacks = Feedback.query.all()
    return render_template('index.html', feedbacks=feedbacks)

@auth_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    content = request.form['feedback']
    new_feedback = Feedback(content=content)
    db.session.add(new_feedback)
    db.session.commit()
    return redirect('/')