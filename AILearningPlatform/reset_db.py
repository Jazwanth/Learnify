"""Script to reset the database with the new schema."""
import os
from app import create_app
from extensions import db
from models import User, Course, Module, QuizQuestion, QuizAttempt, Enrollment, Certificate

def reset_database():
    # Create the Flask application
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Initialize sample data
        from database import init_sample_data
        init_sample_data(app)
        
        print("Database reset successfully!")

if __name__ == "__main__":
    reset_database()
