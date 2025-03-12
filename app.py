from flask import Flask, flash, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash
from controllers.auth import auth_bp
from models.models import Chapter, Question, Quiz, QuizScore, Subject, User, db, Admin, UserResponse  # Import models from models.py
from datetime import date, datetime


# Initialize Flask App
app = Flask(__name__)

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db?check_same_thread=False'
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
                # quiz.date_of_quiz = request.form.get('date_of_quiz')
                date_of_quiz_str = request.form.get('date_of_quiz')  # String from form
                quiz.time_duration = request.form.get('time_duration')
                quiz.remarks = request.form.get('remarks')
                # Convert string to Python date object
                date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()

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
            question_statement = request.form.get('question_statement')
            option_a = request.form.get('option_a')
            option_b = request.form.get('option_b')
            option_c = request.form.get('option_c')
            option_d = request.form.get('option_d')
            correct_option = request.form.get('correct_option')

            new_question = Question(quiz_id=quiz_id, question_statement=question_statement, optionA=option_a, optionB=option_b, optionC=option_c, optionD=option_d, correct_option=correct_option)
            
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')

        return redirect(url_for('admin_dashboard'))

    return render_template('admin_dashboard.html', users=users, subjects=subjects, chapters=chapters, quizzes=quizzes)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    if not user:
        return redirect(url_for('login'))  # Safety check: user must exist
    
    subjects = Subject.query.all()  # Get all subjects
    quizzes = Quiz.query.all()  # Get all quizzes

    return render_template('user_dashboard.html', user=user, subjects=subjects, quizzes=quizzes)


@app.route('/manage_questions', methods=['GET', 'POST'])
def manage_questions():
    if 'admin_logged_in' not in session:
        return redirect(url_for('auth.admin_login'))
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_question':
            quiz_id = request.form.get('quiz_id')
            question_text = request.form.get('question_text')
            optionA = request.form.get('optionA')
            optionB = request.form.get('optionB')
            optionC = request.form.get('optionC')
            optionD = request.form.get('optionD')
            correct_option = request.form.get('correct_option')

            new_question = Question(
                quiz_id=quiz_id,
                question_statement=question_text,
                optionA=optionA,
                optionB=optionB,
                optionC=optionC,
                optionD=optionD,
                correct_option=correct_option
            )


            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')

        elif action == 'delete_question':
            question_id = request.form.get('question_id')
            question = Question.query.get(question_id)
            if question:
                db.session.delete(question)
                db.session.commit()
                flash('Question deleted successfully!', 'danger')

    quizzes = Quiz.query.all()
    questions = Question.query.all()
    return render_template('manage_questions.html', quizzes=quizzes, questions=questions)

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)  # Ensure question exists

    if request.method == 'POST':
        question.question_statement = request.form.get('question_text')
        question.optionA = request.form.get('optionA')
        question.optionB = request.form.get('optionB')
        question.optionC = request.form.get('optionC')
        question.optionD = request.form.get('optionD')
        question.correct_option = request.form.get('correct_option')

        db.session.commit()
        flash('Question updated successfully!', 'info')
        return redirect(url_for('manage_questions'))  # Redirect after updating

    return render_template('edit_question.html', question=question)  # Return response in GET method

@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    user_id = session.get('user_id')  # Ensure the user is logged in
    correct_count = 0

    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            flash('You need to log in to attempt the quiz.', 'error')
            return redirect(url_for('login'))

        feedback = []
        for question in questions:
            selected_answer = request.form.get(f'question_{question.id}', None)  # Default to None if unanswered
            is_correct = selected_answer == question.correct_option
            
            if is_correct:
                correct_count += 1

            feedback.append({
                "question": question.question_statement,
                "selected": selected_answer if selected_answer else "No Answer",
                "correct": question.correct_option,
                "is_correct": is_correct
            })

        user_answers = request.form  # Get all submitted answers
        for question in questions:
            selected_answer = user_answers.get(f'question_{question.id}', 'X')  # Use 'X' for unanswered

             # Store response in database
            user_response = UserResponse(
                user_id=user_id,
                question_id=question.id,
                selected_answer=selected_answer,  # Store 'X' if unanswered
                quiz_id=quiz_id
            )
            db.session.add(user_response)
        
        db.session.commit()
        flash('Quiz submitted successfully!', 'success')
        return render_template('quiz_feedback.html', quiz=quiz, feedback=feedback, correct_count=correct_count, total=len(questions))

    return render_template('attempt_quiz.html', quiz=quiz, questions=questions)

# @app.route('/quiz_feedback/<int:quiz_id>/<int:score>')
# def quiz_feedback(quiz_id, score):
#     quiz = Quiz.query.get(quiz_id)
#     if not quiz:
#         flash("Quiz not found!", "danger")
#         return redirect(url_for("user_dashboard"))

#     total_questions = Question.query.filter_by(quiz_id=quiz_id).count()
#     percentage = (score / total_questions) * 100 if total_questions else 0
    
#     feedback = "Great job!" if percentage >= 80 else "Good effort! Keep practicing!"

#     return render_template("quiz_feedback.html", quiz=quiz, quiz_id=quiz.id, score=score, total_questions=total_questions, percentage=percentage, feedback=feedback)

@app.route('/quiz_feedback/<int:quiz_id>')
def quiz_feedback(quiz_id):
    if 'user_id' not in session:
        flash("Please log in to view quiz feedback.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the quiz
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch all questions related to this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if not questions:
        flash("No questions found for this quiz.", "error")
        return redirect(url_for('dashboard'))

    # Fetch user's responses
    responses = UserResponse.query.filter_by(user_id=user_id, quiz_id=quiz_id).all()

    # Debugging logs
    print(f"Quiz ID: {quiz_id}")
    print(f"Questions found: {len(questions)}")
    print(f"User Responses found: {len(responses)}")

    # Convert responses into a dictionary for quick lookup
    response_dict = {resp.question_id: resp for resp in responses}

    feedback = []
    correct_count = 0

    # Mapping function to get option value from its key (A/B/C/D)
    def get_option_value(question, option_key):
        return getattr(question, f'option{option_key}', "Invalid Option")

    for question in questions:
        user_response = response_dict.get(question.id)
        selected_option_key = user_response.selected_answer if user_response else "No Answer"
        correct_option_key = question.correct_option  # Assuming it's stored as 'A', 'B', 'C', or 'D'

        selected_answer = get_option_value(question, selected_option_key) if user_response else "No Answer"
        correct_answer = get_option_value(question, correct_option_key)

        is_correct = user_response.is_correct if user_response else False

        if is_correct:
            correct_count += 1

        feedback.append({
            "question": question.question_statement,
            "selected": selected_answer,
            "correct": correct_answer,
            "is_correct": is_correct
        })

    total_questions = len(questions)
    percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    return render_template(
        "quiz_feedback.html",
        quiz_id=quiz_id,
        feedback=feedback,
        correct_count=correct_count,
        total=total_questions,
        percentage=round(percentage, 2)
    )

# @app.route('/submit_quiz', methods=['POST'])
# def submit_quiz():

#     user_id = session.get('user_id')
#     quiz_id = request.form.get('quiz_id')
#     print(f"Received quiz_id: {quiz_id}")  # Debugging statement    

#     if not quiz_id:
#         return "Quiz ID is missing", 400

#     quiz = Quiz.query.get(quiz_id)
#     if not quiz:
#         return "Quiz not found", 404
#     total_questions = Question.query.filter_by(quiz_id=quiz_id).count()

    # score = 0
    # for question in quiz.questions:
    #     user_answer = request.form.get(f'question_{question.id}')
    #     if user_answer and user_answer == question.correct_option:
    #         score += 1

    # quiz_score = QuizScore(user_id=user_id, quiz_id=quiz_id, score=score, total_questions=total_questions)
    # db.session.add(quiz_score)
#     db.session.commit()

#     flash('Quiz submitted successfully! Your score has been recorded.', 'success')
#     return redirect(url_for('quiz_feedback', quiz_id=quiz_id, score=score))

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    # Check if a user is logged in
    if 'user_id' not in session:
        flash("Please log in to submit the quiz.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']  # Get user ID from session
    quiz_id = request.form.get('quiz_id')

    if not quiz_id:
        flash("Quiz ID missing!", "error")
        return redirect(url_for('dashboard'))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found!", "error")
        return redirect(url_for('dashboard'))

    # Retrieve submitted answers
    user_answers = request.form.to_dict()
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    total_questions = len(questions)

    # Clear previous responses and scores if re-attempts are allowed
    UserResponse.query.filter_by(user_id=user_id, quiz_id=quiz_id).delete()
    QuizScore.query.filter_by(user_id=user_id, quiz_id=quiz_id).delete()
    db.session.commit()

    score = 0  # Initialize score

    for question in questions:
        selected_answer = user_answers.get(f'question_{question.id}', 'X')  # Default 'X' for unanswered
        is_correct = selected_answer == question.correct_option
        if is_correct:
            score += 1

        # Add latest user response to the database
        user_response = UserResponse(
            user_id=user_id,
            quiz_id=quiz_id,
            question_id=question.id,
            selected_answer=selected_answer,
            is_correct=is_correct
        )        
        db.session.add(user_response)

    # Save quiz score
    quiz_score = QuizScore(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        total_questions=total_questions,
        timestamp=datetime.utcnow()
    )
    db.session.add(quiz_score)

    try:
        db.session.commit()
        flash("Quiz submitted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print("Error saving responses:", e)
        flash("An error occurred while submitting the quiz.", "error")
    finally:
        db.session.close()

    return redirect(url_for('quiz_feedback', quiz_id=quiz_id, score=score))

# Index
@app.route('/')
def home():
    return render_template('index.html')


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

