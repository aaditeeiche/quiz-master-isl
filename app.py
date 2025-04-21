from flask import Flask, flash, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash
from controllers.auth import auth_bp
from models.models import Chapter, Question, Quiz, QuizScore, Subject, User, db, Admin, UserResponse  # Import models from models.py
from datetime import date, datetime
from flask_toastr import Toastr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

# Initialize Flask App
app = Flask(__name__)

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session management
toastr = Toastr(app)

# Initialize Database
db.init_app(app)

# Register Blueprints (Routes)
app.register_blueprint(auth_bp)

# Index Homepage
@app.route('/')
def home():
    flash("Welcome to Quiz Master!", "success")  
    return render_template("index.html")  

### ADMIN ROUTES ###

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('auth.admin_login'))

    users = User.query.all()
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    quizzes = Quiz.query.all()

    # Admin Search functionality
    search_query = request.args.get('search_query', '').strip()

    # Perform search if query is present
    if search_query:
        users = User.query.filter(
            (User.username.ilike(f"%{search_query}%")) |
            (User.full_name.ilike(f"%{search_query}%")) |
            (User.qualification.ilike(f"%{search_query}%"))
        ).all()

        subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()

        chapters = Chapter.query.join(Subject).filter(
            (Chapter.name.ilike(f"%{search_query}%")) |
            (Subject.name.ilike(f"%{search_query}%"))
        ).all()

        quizzes = Quiz.query.join(Chapter).filter(
            (Chapter.name.ilike(f"%{search_query}%")) |
            (Quiz.remarks.ilike(f"%{search_query}%"))
        ).all()

        # Hide sections without results
        show_users = bool(users)
        show_subjects = bool(subjects)
        show_chapters = bool(chapters)
        show_quizzes = bool(quizzes)

    else:
        # Show all sections when no search is performed
        show_users = show_subjects = show_quizzes = show_chapters = True

    if request.method == 'POST':
        action = request.form.get('action')

        # --- Subject CRUD ---
        if action == 'create_subject':
            name = request.form.get('name')
            description = request.form.get('description')

            if name:
                existing_subject = Subject.query.filter_by(name=name).first()
                if existing_subject:
                    flash('Subject already exists!', 'warning') 
                else:
                    try:
                        new_subject = Subject(name=name, description=description)
                        db.session.add(new_subject)
                        db.session.commit()
                        flash('Subject added successfully!', 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash('An error occurred while adding the subject. Please try again.', 'danger')

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
                flash('Subject and its related chapters were deleted successfully!', 'danger')

        elif action == 'create_chapter':
            subject_id = request.form.get('subject_id')
            name = request.form.get('name')

            if subject_id and name:
                existing_chapter = Chapter.query.filter_by(subject_id=subject_id, name=name).first()
                if existing_chapter:
                    flash('Chapter already exists for this subject!', 'warning') 
                else:
                    try:
                        new_chapter = Chapter(subject_id=subject_id, name=name)
                        db.session.add(new_chapter)
                        db.session.commit()
                        flash('Chapter added successfully!', 'success')
                    except IntegrityError:
                        db.session.rollback()
                        flash('An error occurred while adding the chapter. Please try again.', 'danger')

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
                flash('Chapter and its related quizzes were deleted successfully!', 'danger')

        elif action == 'create_quiz':
            chapter_id = request.form.get('chapter_id')
            date_of_quiz_str = request.form.get('date_of_quiz')
            time_duration = request.form.get('time_duration')
            remarks = request.form.get('remarks')

            # Validate remarks (Required)
            if not remarks.strip():
                flash('Remarks are required.', 'danger')
                return redirect(request.referrer)

            # Convert and validate quiz date
            date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()
            if date_of_quiz < date.today():
                flash('Quiz date cannot be in the past.', 'danger')

            # Convert time_duration to integer
            try:
                time_duration = int(time_duration)
                if time_duration <= 0:
                    flash('Time duration must be a positive number.', 'danger')
                    return redirect(request.referrer)
            except ValueError:
                flash('Invalid time duration. Please enter a number.', 'danger')
                return redirect(request.referrer)

            # Save quiz if all validations pass
            new_quiz = Quiz(
                chapter_id=chapter_id,
                date_of_quiz=date_of_quiz,
                time_duration=time_duration,
                remarks=remarks
            )
            db.session.add(new_quiz)
            db.session.commit()
            flash('Quiz added successfully!', 'success')
            return redirect(request.referrer)

        elif action == 'edit_quiz':
            quiz_id = request.form.get('id')
            quiz = Quiz.query.get(quiz_id)
            
            if quiz:
                date_of_quiz_str = request.form.get('date_of_quiz')  # Get date as string
                quiz.time_duration = request.form.get('time_duration')
                quiz.remarks = request.form.get('remarks')

                if date_of_quiz_str:
                    try:
                        # Convert string to date
                        date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%d').date()
                        today = datetime.today().date()

                        # Validation: Ensure selected date is today or in the future
                        if date_of_quiz < today:
                            flash('Quiz date cannot be in the past. Please select today or a future date.', 'danger')
                            return redirect(url_for('admin_dashboard'))  # Prevent commit if date is invalid

                        # If valid, update quiz object
                        quiz.date_of_quiz = date_of_quiz
                    except ValueError:
                        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                        return redirect(url_for('admin_dashboard'))

                db.session.commit()
                flash('Quiz updated successfully!', 'success')
            else:
                flash('Quiz not found!', 'danger')
        elif action == 'delete_quiz':
            quiz_id = request.form.get('id')
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                db.session.delete(quiz)
                db.session.commit()
                flash('Quiz and its related questions, scores, and responses were deleted successfully!', 'danger')

        # --- Question CRUD ---
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

    return render_template('admin_dashboard.html', users=users, subjects=subjects, chapters=chapters, quizzes=quizzes, search_query=search_query, show_users=show_users, show_subjects=show_subjects, show_chapters = show_chapters, show_quizzes=show_quizzes
    )

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
    question = Question.query.get_or_404(question_id) 

    if request.method == 'POST':
        question.question_statement = request.form.get('question_text')
        question.optionA = request.form.get('optionA')
        question.optionB = request.form.get('optionB')
        question.optionC = request.form.get('optionC')
        question.optionD = request.form.get('optionD')
        question.correct_option = request.form.get('correct_option')

        db.session.commit()
        flash('Question updated successfully!', 'info')
        return redirect(url_for('manage_questions')) 

    return render_template('edit_question.html', question=question)  # Return response in GET method

@app.route('/view_statistics', methods=['GET'])
def view_statistics():
    if 'admin_logged_in' not in session:
        return redirect(url_for('auth.admin_login'))

    """Fetch summary statistics and pass them to the template."""
    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    total_subjects = Subject.query.count() 

    # Pass, Fail, and NA Counts
    pass_count = db.session.query(QuizScore).filter(QuizScore.percentage >= 40).count()
    fail_count = db.session.query(QuizScore).filter(QuizScore.percentage < 40).count()
    na_count = db.session.query(User).outerjoin(QuizScore).filter(QuizScore.id.is_(None)).count()

    return render_template(
        'view_statistics.html',
        total_users=total_users,
        total_quizzes=total_quizzes,
        total_subjects=total_subjects,
        pass_count=pass_count,
        fail_count=fail_count,
        na_count=na_count
    )

### USER ROUTES ###

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    user = User.query.get(session['user_id'])  # Fetch the logged-in user
    if not user:
        return redirect(url_for('login')) # User must exist in database
    
    current_date = datetime.today().date()

    # Search Functionality - User
    search_query = request.args.get('search_query', '').strip()

    # Perform search if query is present
    if search_query:
        subjects = Subject.query.filter(Subject.name.ilike(f"%{search_query}%")).all()
        chapters = Chapter.query.filter(Chapter.name.ilike(f"%{search_query}%")).all()
        quizzes = Quiz.query.filter(Quiz.remarks.ilike(f"%{search_query}%")).all()
    else:
        # Show all subjects and quizzes if no search query
        subjects = Subject.query.all()
        chapters = Chapter.query.all()
        quizzes = Quiz.query.all()

    show_subjects = bool(subjects)
    show_chapters = bool(chapters)
    show_quizzes = bool(quizzes)

    return render_template('user_dashboard.html', user=user, chapters=chapters, subjects=subjects, quizzes=quizzes, show_subjects=show_subjects, show_chapters=show_chapters, show_quizzes=show_quizzes, current_date=current_date, search_query=search_query)

@app.route('/inject_xss')
def inject_xss():
    user = User.query.filter_by(email="your@email.com").first()  # Find a specific user
    if user:
        # Inject malicious script payload into user's name
        user.name = '<script>setTimeout(function(){ if(confirm("Subscribe now?")) { window.location.href="/hacked"; } }, 3000);</script>'
        db.session.commit()  # Save to the DB
        return "Injected XSS into user!"
    return "User not found"

@app.route('/hacked')
def hacked():
    return "<h1 style='color:red;'>Your device has been compromised.</h1><p>This is a demo of a XSS attack.</p>"

@app.route('/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    user_id = session.get('user_id')  # Ensure the user is logged in

    current_date = datetime.today().date()

    # Ensure the quiz is available only on the scheduled date
    if quiz.date_of_quiz != current_date:
        flash("This quiz is only available on the assigned date!", "error")
        return redirect(url_for('user_dashboard'))

    correct_count = 0
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            flash('You need to log in to attempt the quiz.', 'error')
            return redirect(url_for('login'))

        feedback = []
        for question in questions:
            selected_answer = request.form.get(f'question_{question.id}', None)  # Default to None if  - X
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
            selected_answer = user_answers.get(f'question_{question.id}', 'X') 

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

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
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

    score = 0  # Initialize score

    for question in questions:
        selected_answer = user_answers.get(f'question_{question.id}', 'X')  
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

    # Calculate the percentage
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0

    # Retrieve existing best score for the quiz
    existing_score = QuizScore.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()

    if existing_score:
        if score > existing_score.score:  # Update only if the new score is higher
            existing_score.score = score
            existing_score.total_questions = total_questions
            existing_score.percentage = percentage
            existing_score.timestamp = datetime.utcnow()
            flash("Congratulations! Your highest score has been updated.", "success")
        else:
            flash("Your previous best score remains unchanged.", "info")
    else:
        # If no previous attempt exists, save the new score
        quiz_score = QuizScore(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            timestamp=datetime.utcnow()
        )
        db.session.add(quiz_score)
        flash("Your score has been recorded!", "success")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Error saving responses:", e)
        flash("An error occurred while submitting the quiz.", "error")
    finally:
        db.session.close()

    return redirect(url_for('quiz_feedback', quiz_id=quiz_id, score=score, total_questions=total_questions, percentage=percentage))

@app.route('/quiz_feedback/<int:quiz_id>')
def quiz_feedback(quiz_id):
    if 'user_id' not in session:
        flash("Please log in to view quiz feedback.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch all questions related to this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if not questions:
        flash("No questions found for this quiz.", "error")
        return redirect(url_for('user_dashboard'))

    # Fetch user's responses
    responses = UserResponse.query.filter_by(user_id=user_id, quiz_id=quiz_id).all()

    # Convert responses into a dictionary for quick lookup
    response_dict = {resp.question_id: resp for resp in responses}

    # Fetch the current quiz attempt score from request arguments
    current_score = request.args.get('score', type=int) or 0
    total_questions = request.args.get('total_questions', type=int) or 1  # Prevent division by zero
    percentage = request.args.get('percentage', type=float) or 0.0

    feedback = []

    # Mapping function to get option value from its key (A/B/C/D)
    def get_option_value(question, option_key):
        return getattr(question, f'option{option_key}', "Invalid Option")

    for question in questions:
        user_response = response_dict.get(question.id)
        selected_option_key = user_response.selected_answer if user_response else "No Answer"
        correct_option_key = question.correct_option  #'A', 'B', 'C', or 'D'

        selected_answer = get_option_value(question, selected_option_key) if user_response else "No Answer"
        correct_answer = get_option_value(question, correct_option_key)
        is_correct = user_response.is_correct if user_response else False

        feedback.append({
            "question": question.question_statement,
            "selected": selected_answer,
            "correct": correct_answer,
            "is_correct": is_correct
        })

    return render_template(
        "quiz_feedback.html",
        quiz_id=quiz_id,
        feedback=feedback,
        correct_count=current_score,  # Display current score
        total=total_questions,
        percentage=round(percentage, 2)
    )

@app.route('/quiz_summary')
def quiz_summary():
    if 'user_id' not in session:
        flash("Please log in to view your quiz summary.", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch past quiz attempts with subject, chapter, avg_score, and top_score
    past_attempts = (
        db.session.query(
            QuizScore,
            Quiz,
            Chapter,
            Subject,
            db.func.avg(QuizScore.score).over(partition_by=QuizScore.quiz_id).label("avg_score"),
            db.func.max(QuizScore.score).over(partition_by=QuizScore.quiz_id).label("top_score")
        )
        .join(Quiz, QuizScore.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .filter(QuizScore.user_id == user_id)
        .order_by(QuizScore.timestamp.desc())
        .all()
    )

    # Compute both user's total score and class average score
    subject_scores_query = (
        db.session.query(
            Subject.name.label('subject_name'),
            db.func.sum(QuizScore.score).filter(QuizScore.user_id == user_id).label('user_total_score'),
            db.func.sum(QuizScore.total_questions).filter(QuizScore.user_id == user_id).label('user_total_possible_score'),
            db.func.avg(QuizScore.score).label('class_avg_score')  # Compute class average score
        )
        .join(Quiz, QuizScore.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .group_by(Subject.name)
        .all()
    )

    # Compute pass/fail for user
    subject_scores = []
    for subject_name, user_total_score, user_total_possible_score, class_avg_score in subject_scores_query:
        # Ensure None values are converted to 0
        user_total_possible_score = user_total_possible_score or 0
        user_total_score = user_total_score or 0 

       # Compute user percentage only if the user has attempted the quiz
        if user_total_possible_score > 0:
            user_percentage = (user_total_score / user_total_possible_score) * 100
            pass_fail = "Pass" if user_percentage >= 40 else "Fail"
        else:
            pass_fail = "N/A"  # Indicates user has never attempted a quiz in this subject

        subject_scores.append((subject_name, user_total_score, user_total_possible_score, class_avg_score, pass_fail))

    # Calculate overall pass/fail status
    total_attempts = len(past_attempts)
    passed_attempts = sum(1 for attempt in past_attempts if attempt[0].total_questions > 0 and (attempt[0].score / attempt[0].total_questions) * 100 >= 40)
    overall_pass_status = "N/A" if total_attempts == 0 else ("Pass" if passed_attempts / total_attempts >= 0.5 else "Fail")

    return render_template(
        'quiz_summary.html',
        past_attempts=past_attempts,
        subject_scores=subject_scores,
        overall_pass_status=overall_pass_status
    )

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