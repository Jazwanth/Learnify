"""
Utility functions for the e-learning platform.
"""
import datetime
import json
import random
import logging
from models import Progress, Module, Enrollment

def format_date(date_str, format="%Y-%m-%d"):
    """Format a date string to a more readable format"""
    try:
        date_obj = datetime.datetime.strptime(date_str, format)
        return date_obj.strftime("%b %d, %Y")
    except:
        return date_str

def calculate_progress(user_id, course_id):
    """Calculate the overall completion percentage for a user in a specific course.
    Returns a float between 0.0 and 1.0.
    """
    # Get all modules for the given course
    course_modules = Module.query.filter_by(course_id=course_id).all()
    total_modules_in_course = len(course_modules)

    if total_modules_in_course == 0:
        return 0.0 # No modules in the course, so 0% progress

    # Get user's progress for all modules in this course
    # A module is considered completed if its progress.completion is 1.0 (or very close)
    completed_module_count = 0
    for module in course_modules:
        module_progress = Progress.query.filter_by(
            user_id=user_id,
            course_id=course_id,
            module_id=module.id
        ).first()
        if module_progress and module_progress.completion >= 1.0: # Using >= 1.0 to handle potential float inaccuracies if progress can exceed 1.0
            completed_module_count += 1
    
    if total_modules_in_course == 0: # Should be caught above, but defensive check
        return 0.0
        
    return float(completed_module_count) / total_modules_in_course

def get_badge_svg_path(achievement_id):
    """Get the path to the SVG for a specific achievement badge"""
    # Map achievement IDs to badge SVG elements
    badge_map = {
        'first_course': 0,    # First Steps
        'course_complete': 1, # Course Graduate
        'quiz_perfect': 2,    # Perfect Score
        'streak_7': 3,        # Weekly Warrior
        'streak_30': 4,       # Monthly Master
        'complete_5': 5       # Learning Enthusiast
    }
    
    # Return the index or a default if not found
    return badge_map.get(achievement_id, 0)

def generate_recommendation(user_courses, all_courses):
    """Generate course recommendations based on user's enrolled courses"""
    enrolled_ids = [course['id'] for course in user_courses]
    recommended = []
    
    for course in all_courses:
        if course['id'] not in enrolled_ids:
            recommended.append(course)
    
    # Shuffle and return the top 2 recommendations
    random.shuffle(recommended)
    return recommended[:2]

def is_admin(user):
    """Check if a user has admin role"""
    if not user:
        return False
    return user.get('role', '') == 'admin'

def get_streak_message(streak):
    """Get a motivational message based on streak count"""
    if streak == 0:
        return "Start your learning streak today!"
    elif streak == 1:
        return "First day of your learning streak!"
    elif streak < 7:
        return f"You're on a {streak}-day streak! Keep going!"
    elif streak < 30:
        return f"Amazing! {streak}-day learning streak!"
    else:
        return f"Incredible! {streak}-day streak - you're unstoppable!"
