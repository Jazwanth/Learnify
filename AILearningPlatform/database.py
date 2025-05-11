"""
Database module for the e-learning platform.
This module provides functions to initialize the database with sample data.
"""
import datetime
import json
import logging
from extensions import db
from werkzeug.security import generate_password_hash
from models import User, Course, Module, Quiz, Enrollment, Progress
from models import Achievement, UserAchievement, Streak, ChatMessage, Certificate

def init_sample_data(app):
    """Initialize the database with sample data if it's empty"""
    # This function will now be called from within an active app_context in app.py
    # Add sample courses if none exist
    if Course.query.first() is None:
        add_sample_courses()
        add_sample_achievements()
        logging.debug("Database initialized with sample courses and achievements")
    else:
        logging.debug("Database already contains data - skipping initialization")

def add_sample_courses():
    """Add sample course data to the database using SQLAlchemy models"""
    # Course 1: Python Programming
    python_course = Course(
        title='Introduction to Python Programming',
        description='Learn the basics of Python programming language.',
        image_url='images/py.jpg',
        instructor='Dr. Python',
        duration='4 weeks',
        level='Beginner'
    )
    db.session.add(python_course)
    db.session.flush()  # Get the course ID without committing
    
    # Add modules for Python course
    module1 = Module(
        course_id=python_course.id,
        title='Getting Started with Python',
        content='Python is a high-level, interpreted programming language...',
        video_url='https://www.youtube.com/embed/kqtD5dpn9C8',
        order=1
    )
    db.session.add(module1)
    db.session.flush()
    
    # Add quizzes for module 1
    quiz1 = Quiz(
        module_id=module1.id,
        question='What is Python?',
        _options=json.dumps(['A snake', 'A programming language', 'A type of coffee', 'A video game']),
        answer='1'
    )
    quiz2 = Quiz(
        module_id=module1.id,
        question='Who created Python?',
        _options=json.dumps(['Guido van Rossum', 'Bill Gates', 'Elon Musk', 'Steve Jobs']),
        answer='0'
    )
    db.session.add(quiz1)
    db.session.add(quiz2)
    
    # Add module 2 for Python course
    module2 = Module(
        course_id=python_course.id,
        title='Variables and Data Types',
        content='Variables are used to store data values...',
        video_url='https://www.youtube.com/embed/cQT33rt_9TE',
        order=2
    )
    db.session.add(module2)
    db.session.flush()
    
    # Add quizzes for module 2
    quiz3 = Quiz(
        module_id=module2.id,
        question='Which of the following is a valid variable name in Python?',
        _options=json.dumps(['123var', '$var', 'var_123', 'var 123']),
        answer='2'
    )
    quiz4 = Quiz(
        module_id=module2.id,
        question='What is the output of print(type(42))?',
        _options=json.dumps(['<class \'int\'>', '<class \'str\'>', '<class \'float\'>', '<class \'bool\'>']),
        answer='0'
    )
    db.session.add(quiz3)
    db.session.add(quiz4)
    
    # Course 2: Data Science
    data_course = Course(
        title='Data Science Fundamentals',
        description='Learn the basics of data science and analysis.',
        image_url='images/ds.jpg',
        instructor='Dr. Data',
        duration='6 weeks',
        level='Intermediate'
    )
    db.session.add(data_course)
    db.session.flush()
    
    # Add module for Data Science course
    ds_module = Module(
        course_id=data_course.id,
        title='Introduction to Data Science',
        content='Data Science combines multiple fields including statistics, scientific methods...',
        video_url='https://www.youtube.com/embed/X3paOmcrTjQ',
        order=1
    )
    db.session.add(ds_module)
    db.session.flush()
    
    # Add quizzes for Data Science module
    ds_quiz1 = Quiz(
        module_id=ds_module.id,
        question='What is Data Science?',
        _options=json.dumps(['A programming language', 'An interdisciplinary field using scientific methods to extract knowledge from data', 'A database system', 'A web development framework']),
        answer='1'
    )
    ds_quiz2 = Quiz(
        module_id=ds_module.id,
        question='Which of these is NOT a common data science tool?',
        _options=json.dumps(['Python', 'R', 'Tableau', 'Adobe Photoshop']),
        answer='3'
    )
    db.session.add(ds_quiz1)
    db.session.add(ds_quiz2)
    
    # Course 3: Machine Learning
    ml_course = Course(
        title='Machine Learning Basics',
        description='Introduction to machine learning concepts and algorithms.',
        image_url='images/ml.jpg',
        instructor='Dr. ML',
        duration='8 weeks',
        level='Advanced'
    )
    db.session.add(ml_course)
    db.session.flush()
    
    # Add module for Machine Learning course
    ml_module = Module(
        course_id=ml_course.id,
        title='What is Machine Learning?',
        content='Machine learning is a subset of artificial intelligence...',
        video_url='https://www.youtube.com/embed/ukzFI9rgwfU',
        order=1
    )
    db.session.add(ml_module)
    db.session.flush()
    
    # Add quizzes for Machine Learning module
    ml_quiz1 = Quiz(
        module_id=ml_module.id,
        question='What is supervised learning?',
        _options=json.dumps(['Learning without a teacher', 'Learning with labeled data', 'Learning through reinforcement', 'Learning by clustering']),
        answer='1'
    )
    ml_quiz2 = Quiz(
        module_id=ml_module.id,
        question='Which algorithm is NOT a classification algorithm?',
        _options=json.dumps(['Logistic Regression', 'Decision Trees', 'K-means', 'Random Forest']),
        answer='2'
    )
    db.session.add(ml_quiz1)
    db.session.add(ml_quiz2)
    
    # Course 4: Web Development
    web_course = Course(
        title='Web Development with HTML & CSS',
        description='Learn how to build responsive websites with HTML and CSS.',
        image_url='images/hc.jpg',
        instructor='Prof. Web',
        duration='5 weeks',
        level='Beginner'
    )
    db.session.add(web_course)
    db.session.flush()
    
    # Add module for Web Development course
    web_module = Module(
        course_id=web_course.id,
        title='HTML Basics',
        content='HTML (HyperText Markup Language) is the standard markup language for documents...',
        video_url='https://www.youtube.com/embed/qz0aGYrrlhU',
        order=1
    )
    db.session.add(web_module)
    db.session.flush()
    
    # Add quizzes for Web Development module
    web_quiz1 = Quiz(
        module_id=web_module.id,
        question='What does HTML stand for?',
        _options=json.dumps(['Hyper Text Markup Language', 'High Tech Modern Language', 'Hyper Transfer Markup Language', 'Home Tool Markup Language']),
        answer='0'
    )
    web_quiz2 = Quiz(
        module_id=web_module.id,
        question='Which tag is used to define a paragraph in HTML?',
        _options=json.dumps(['<paragraph>', '<p>', '<para>', '<text>']),
        answer='1'
    )
    db.session.add(web_quiz1)
    db.session.add(web_quiz2)
    
    # Commit all the changes
    db.session.commit()
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@example.com',
        role='admin'
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    db.session.commit()

def add_sample_achievements():
    """Add sample achievements to the database"""
    achievements = [
        {
            'title': 'First Steps',
            'description': 'Enrolled in your first course',
            'badge_id': 'badge-first-steps'
        },
        {
            'title': 'Course Graduate',
            'description': 'Completed your first course',
            'badge_id': 'badge-course-graduate'
        },
        {
            'title': 'Perfect Score',
            'description': 'Scored 100% on a quiz',
            'badge_id': 'badge-perfect-score'
        },
        {
            'title': 'Weekly Warrior',
            'description': 'Maintained a 7-day learning streak',
            'badge_id': 'badge-weekly-warrior'
        },
        {
            'title': 'Monthly Master',
            'description': 'Maintained a 30-day learning streak',
            'badge_id': 'badge-monthly-master'
        },
        {
            'title': 'Learning Enthusiast',
            'description': 'Completed 5 courses',
            'badge_id': 'badge-learning-enthusiast'
        }
    ]
    
    for achievement_data in achievements:
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
    
    db.session.commit()
