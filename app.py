from flask import Flask, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash
from controllers.auth import auth_bp
from models.models import db, Admin  # Import models from models.py


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

# Admin Dashboard Route
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('auth.admin_login'))
    return render_template('admin_dashboard.html')

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
