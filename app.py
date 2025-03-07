from flask import Flask
from werkzeug.security import generate_password_hash
from models.models import db, Admin  # Import models from models.py

# Initialize Flask App
app = Flask(__name__)

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

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
