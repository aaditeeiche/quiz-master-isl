from flask import Flask, flash, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash
from controllers.auth import auth_bp
from models.models import Chapter, Question, Quiz, Subject, User, db, Admin  # Import models from models.py
from datetime import date, datetime


# Initialize Flask App
app = Flask(__name__)

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session management


# Initialize Database
db.init_app(app)

# Register Blueprints (Routes)
app.register_blueprint(auth_bp)

# Admin Dashboard
@app.route('/admin_dashboard', methods=['GET', 'POST'])
# def admin_dashboard():
#     if 'admin_logged_in' not in session:
#         return redirect(url_for('auth.admin_login'))

#     users = User.query.all()  # Fetch all users from the database
#     return render_template('admin_dashboard.html', users=users)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('auth.admin_login'))

    users = User.query.all()
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quizzes = Quiz.query.all()

    if request.method == 'POST':
        action = request.form.get('action')

        # --- Subject CRUD ---
        if action == 'create_subject':
            name = request.form.get('name')
            description = request.form.get('description')
            if name:
                new_subject = Subject(name=name, description=description)
                db.session.add(new_subject)
                db.session.commit()
                flash('Subject added successfully!', 'success')

        elif action == 'edit_subject':
            subject_id = request.form.get('id')
            name = request.form.get('name')
            description = request.form.get('description')
            subject = Subject.query.get(subject_id)
            if subject:
                subject.name = name
                subject.description = description
                db.session.commit()
                flash('Subject updated successfully!', 'success')

        elif action == 'delete_subject':
            subject_id = request.form.get('id')
            subject = Subject.query.get(subject_id)
            if subject:
                db.session.delete(subject)
                db.session.commit()
                flash('Subject deleted successfully!', 'success')

        # --- Chapter CRUD ---
        elif action == 'create_chapter':
            subject_id = request.form.get('subject_id')
            name = request.form.get('name')
            if subject_id and name:
                new_chapter = Chapter(subject_id=subject_id, name=name)
                db.session.add(new_chapter)
                db.session.commit()
                flash('Chapter added successfully!', 'success')

        elif action == 'edit_chapter':
            chapter_id = request.form.get('id')
            chapter = Chapter.query.get(chapter_id)
            if chapter:
                chapter.name = request.form.get('name')
                db.session.commit()
                flash('Chapter updated successfully!', 'success')

        elif action == 'delete_chapter':
            chapter_id = request.form.get('id')
            chapter = Chapter.query.get(chapter_id)
            if chapter:
                db.session.delete(chapter)
                db.session.commit()
                flash('Chapter deleted successfully!', 'success')

        # --- Quiz CRUD ---
        elif action == 'create_quiz':
            chapter_id = request.form.get('chapter_id')
            date_of_quiz_str = request.form.get('date_of_quiz')  # String from form
            time_duration = request.form.get('time_duration')
            remarks = request.form.get('remarks')

            # Convert string to Python date object
            date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()

            # Convert time_duration to integer (assuming minutes)
            try:
                time_duration = int(time_duration)  # Convert to integer
            except ValueError:
                flash('Invalid time duration. Please enter a number.', 'danger')
                return redirect(request.referrer)  # Redirect back if invalid input

            new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, time_duration=time_duration, remarks=remarks)
            db.session.add(new_quiz)
            db.session.commit()
            flash('Quiz added successfully!', 'success')

        elif action == 'edit_quiz':
            quiz_id = request.form.get('id')
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                quiz.date_of_quiz = request.form.get('date_of_quiz')
                quiz.time_duration = request.form.get('time_duration')
                quiz.remarks = request.form.get('remarks')
                db.session.commit()
                flash('Quiz updated successfully!', 'success')

        elif action == 'delete_quiz':
            quiz_id = request.form.get('id')
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                db.session.delete(quiz)
                db.session.commit()
                flash('Quiz deleted successfully!', 'success')

        # --- Quiz CRUD ---
        elif action == 'create_question':
            quiz_id = request.form.get('quiz_id')
            question_text = request.form.get('question_text')
            option_a = request.form.get('option_a')
            option_b = request.form.get('option_b')
            option_c = request.form.get('option_c')
            option_d = request.form.get('option_d')
            correct_answer = request.form.get('correct_answer')

            new_question = Question(quiz_id=quiz_id, question_statement=question_text, optionA=option_a, optionB=option_b, optionC=option_c, optionD=option_d, correct_option=correct_answer)
            
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')

        return redirect(url_for('admin_dashboard'))

        


    return render_template('admin_dashboard.html', users=users, subjects=subjects, chapters=chapters, quizzes=quizzes)

# User Dashboard Route
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.user_login'))
    return render_template('user_dashboard.html')

# Create Database Tables and Pre-Fill Admin
with app.app_context():
    db.create_all()

    # Check if admin exists, if not, create one
    if not Admin.query.first():
        admin_user = Admin(username="quizmaster", password=generate_password_hash("admin123"))
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
