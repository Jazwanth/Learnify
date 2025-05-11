"""
Routes for the e-learning platform.
"""
import logging
import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, current_app, abort, send_file, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # Added for file uploads
import os # Added for file uploads
import uuid # Added for unique filenames
from datetime import datetime, timedelta

from extensions import db  # Updated import
from models import User, Course, Module, Quiz, Enrollment, Progress, Achievement, UserAchievement, Streak, Certificate, ChatMessage, QuizQuestion, QuizAttempt
from chatbot import get_chatbot_response
from utils import format_date, calculate_progress, is_admin, generate_recommendation, get_streak_message
from certificate_generator import generate_certificate # Added for certificate generation

# Create blueprint
routes_bp = Blueprint('routes', __name__)

# Admin check decorator
def admin_required(f):
    """Decorator to require admin role for certain routes"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@routes_bp.route('/')
def index():
    """Home page route"""
    # Get featured courses
    courses = Course.query.limit(3).all()  # Just show first 3 courses on homepage
    
    return render_template('index.html', courses=courses)

# Login route
@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate form data
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Update streak
            streak = Streak.query.filter_by(user_id=user.id).first()
            if not streak:
                streak = Streak(user_id=user.id)
                db.session.add(streak)
            
            # Check if it's a new day
            today = datetime.now().date()
            last_login = streak.last_login.date() if streak.last_login else None
            
            if last_login != today:
                if last_login and (today - last_login).days == 1:
                    # Consecutive day
                    streak.current_streak += 1
                    if streak.current_streak > streak.max_streak:
                        streak.max_streak = streak.current_streak
                        # Check for streak achievements
                        if streak.max_streak == 7:
                            # Weekly warrior achievement
                            weekly_badge = Achievement.query.filter_by(badge_id='badge-weekly-warrior').first()
                            if weekly_badge and not UserAchievement.query.filter_by(
                                    user_id=user.id, achievement_id=weekly_badge.id).first():
                                user_achievement = UserAchievement(
                                    user_id=user.id, 
                                    achievement_id=weekly_badge.id
                                )
                                db.session.add(user_achievement)
                                flash(f'Achievement unlocked: {weekly_badge.title}!', 'success')
                        
                        elif streak.max_streak == 30:
                            # Monthly master achievement
                            monthly_badge = Achievement.query.filter_by(badge_id='badge-monthly-master').first()
                            if monthly_badge and not UserAchievement.query.filter_by(
                                    user_id=user.id, achievement_id=monthly_badge.id).first():
                                user_achievement = UserAchievement(
                                    user_id=user.id, 
                                    achievement_id=monthly_badge.id
                                )
                                db.session.add(user_achievement)
                                flash(f'Achievement unlocked: {monthly_badge.title}!', 'success')
                elif last_login and (today - last_login).days > 1:
                    # Streak broken
                    streak.current_streak = 1
                
                streak.last_login = datetime.now()
            
            db.session.commit()
            
            # Log the user in
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            
            # Get streak message if applicable
            if streak and streak.current_streak > 1:
                streak_msg = get_streak_message(streak.current_streak)
                flash(streak_msg, 'info')
            
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

# Register route
@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register route"""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not username or not email or not password or not confirm_password:
            flash('Please fill out all fields', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            role='student'
        )
        new_user.set_password(password)
        
        # Add user to session and flush to get the user ID
        db.session.add(new_user)
        db.session.flush()
        
        # Initialize streak with the user ID
        new_streak = Streak(
            user_id=new_user.id,
            current_streak=1,
            max_streak=1,
            last_login=datetime.now()
        )
        
        db.session.add(new_streak)
        db.session.commit()
        
        # Log the user in
        login_user(new_user)
        flash(f'Welcome, {username}! Your account has been created.', 'success')
        
        return redirect(url_for('routes.dashboard'))
    
    return render_template('register.html')

# Logout route
@routes_bp.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('routes.index'))

# Dashboard route
@routes_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    # Get user's enrolled courses
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    
    enrolled_courses = []
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            course_data = {
                'id': course.id,
                'title': course.title,
                'image_url': course.image_url,
                'level': course.level,
                'completion': enrollment.completion,
                'instructor': course.instructor,
                'last_module': enrollment.last_module
            }
            enrolled_courses.append(course_data)
    
    # Get course recommendations
    all_courses = Course.query.all()
    recommendations = []
    if len(enrolled_courses) < len(all_courses):
        already_enrolled = set(e.course_id for e in enrollments)
        recommendations = [c for c in all_courses if c.id not in already_enrolled][:2]  # Recommend up to 2 courses
    
    # Get user achievements
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    achievements = []
    for ua in user_achievements:
        achievement = Achievement.query.get(ua.achievement_id)
        if achievement:
            achievements.append({
                'title': achievement.title,
                'description': achievement.description,
                'badge_id': achievement.badge_id,
                'earned_date': format_date(ua.earned_date.strftime('%Y-%m-%d'))
            })
    
    # Get user's streak
    streak = Streak.query.filter_by(user_id=current_user.id).first()
    streak_data = {
        'current': streak.current_streak if streak else 0,
        'max': streak.max_streak if streak else 0
    }
    
    return render_template(
        'dashboard.html',
        user=current_user,
        enrolled_courses=enrolled_courses,
        achievements=achievements,
        streak=streak_data,
        recommendations=recommendations
    )

# Courses route
@routes_bp.route('/courses')
def courses():
    """All courses route"""
    all_courses = Course.query.all()
    
    # Check which courses the user is enrolled in, if logged in
    enrolled_course_ids = set()
    if current_user.is_authenticated:
        enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
        enrolled_course_ids = {e.course_id for e in enrollments}
        
    # Prepare data for template
    courses_data = []
    for course in all_courses:
        course_data = {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'image_url': course.image_url,
            'instructor': course.instructor,
            'duration': course.duration,
            'level': course.level,
            'module_count': course.modules.count(),
            'enrolled': course.id in enrolled_course_ids
        }
        courses_data.append(course_data)
    
    return render_template('courses.html', courses=courses_data)

# Course details route
@routes_bp.route('/course/<int:course_id>')
def course_details(course_id):
    """Course details route"""
    course = Course.query.get_or_404(course_id)
    
    # Check if user is enrolled
    enrolled = False
    progress = None
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id, course_id=course_id
        ).first()
        
        if enrollment:
            enrolled = True
            progress = {
                'completion': enrollment.completion,
                'last_module': enrollment.last_module
            }
    
    # Get modules with their quizzes
    modules = []
    for module in course.modules.order_by(Module.order):
        quizzes = []
        for quiz in module.quiz:
            quizzes.append({
                'id': quiz.id,
                'question': quiz.question,
                'options': quiz.options,
                'answer': quiz.answer
            })
        
        modules.append({
            'id': module.id,
            'title': module.title,
            'content': module.content,
            'video_url': module.video_url,
            'quiz': quizzes
        })
    
    # Prepare course data
    course_data = {
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'image_url': course.image_url,
        'instructor': course.instructor,
        'duration': course.duration,
        'level': course.level,
        'modules': modules
    }
    
    return render_template(
        'course_details.html', 
        course=course_data, 
        enrolled=enrolled, 
        progress=progress
    )

# Enroll in course route
@routes_bp.route('/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    """Enroll in course route"""
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course', 'warning')
        return redirect(url_for('routes.course_details', course_id=course_id))
    
    # Create new enrollment
    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
        enrollment_date=datetime.now(),
        completion=0,
        last_module=0
    )
    db.session.add(enrollment)
    
    # Check if this is the user's first course (achievement)
    enrollment_count = Enrollment.query.filter_by(user_id=current_user.id).count()
    if enrollment_count == 0:  # This will be the first after commit
        first_steps = Achievement.query.filter_by(badge_id='badge-first-steps').first()
        if first_steps:
            user_achievement = UserAchievement(
                user_id=current_user.id,
                achievement_id=first_steps.id,
                earned_date=datetime.now()
            )
            db.session.add(user_achievement)
            flash(f'Achievement unlocked: {first_steps.title}!', 'success')
    
    db.session.commit()
    
    flash(f'You have enrolled in {course.title}!', 'success')
    return redirect(url_for('routes.course_details', course_id=course_id))

# Update course progress route (AJAX)
@routes_bp.route('/api/update-progress', methods=['POST'])
@login_required
def update_course_progress():
    """Update course progress API"""
    data = request.json
    
    course_id = data.get('course_id')
    module_id = data.get('module_id') # This is the specific module being updated
    module_completion_input = data.get('completion', 0) # Progress for this specific module
    quiz_score_input = data.get('quiz_score') # Score for this specific module's quiz, if any
    
    if not course_id or not module_id:
        return jsonify({'status': 'error', 'message': 'Missing required fields (course_id or module_id)'}), 400
    
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first()
    
    if not enrollment:
        return jsonify({'status': 'error', 'message': 'Not enrolled in this course'}), 403

    # Update or create progress for the specific module
    module_progress = Progress.query.filter_by(
        user_id=current_user.id, course_id=course_id, module_id=module_id
    ).first()

    if module_progress:
        module_progress.completion = module_completion_input
        if quiz_score_input is not None:
            module_progress.quiz_score = quiz_score_input
    else:
        module_progress = Progress(
            user_id=current_user.id,
            course_id=course_id,
            module_id=module_id,
            completion=module_completion_input,
            quiz_score=quiz_score_input
        )
        db.session.add(module_progress)
    
    # db.session.flush() # Ensure module_progress is persisted if needed by calculate_progress immediately

    achievement_awarded_details = None

    # 1. Check for Perfect Score Achievement (for the current module's quiz)
    if quiz_score_input == 100:
        perfect_score_badge = Achievement.query.filter_by(badge_id='badge-perfect-score').first()
        if perfect_score_badge and not UserAchievement.query.filter_by(
                user_id=current_user.id, achievement_id=perfect_score_badge.id).first():
            user_achievement = UserAchievement(
                user_id=current_user.id, 
                achievement_id=perfect_score_badge.id,
                earned_date=datetime.now()
            )
            db.session.add(user_achievement)
            achievement_awarded_details = {
                'title': perfect_score_badge.title,
                'description': perfect_score_badge.description
            }
            # flash(f'Achievement unlocked: {perfect_score_badge.title}!', 'success') # Flashing handled by frontend based on JSON

    # 2. Recalculate and update overall course completion in Enrollment
    # This utility function should query all Progress for the user in this course
    overall_course_completion_float = calculate_progress(current_user.id, course_id) 
    enrollment.completion = overall_course_completion_float # Update overall course completion
    enrollment.last_module = module_id # Update last accessed module in the course

    # 3. Check for Course Completion Achievement & set completed_at timestamp
    if overall_course_completion_float == 1.0 and enrollment.completed_at is None:
        enrollment.completed_at = datetime.now()
        course_graduate_badge = Achievement.query.filter_by(badge_id='badge-course-graduate').first()
        if course_graduate_badge and not UserAchievement.query.filter_by(
                user_id=current_user.id, achievement_id=course_graduate_badge.id).first():
            user_achievement = UserAchievement(
                user_id=current_user.id, 
                achievement_id=course_graduate_badge.id,
                earned_date=datetime.now()
            )
            db.session.add(user_achievement)
            # Overwrite or append to achievement_awarded_details if needed.
            # For now, course graduate achievement takes precedence if perfect score was also on the last module.
            achievement_awarded_details = {
                'title': course_graduate_badge.title,
                'description': course_graduate_badge.description
            }
            # flash(f'Achievement unlocked: {course_graduate_badge.title}!', 'success')

    db.session.commit()

    response_data = {'status': 'success', 'message': 'Progress updated'}
    if achievement_awarded_details:
        response_data['achievement'] = achievement_awarded_details
    
    return jsonify(response_data)

# Store connected clients for SSE
leaderboard_clients = []

def stream_leaderboard():
    """Generate and stream leaderboard data to connected clients"""
    def event_stream():
        while True:
            try:
                # Get leaderboard data
                leaderboard_data = get_leaderboard_data()
                
                # Format as SSE
                data = json.dumps(leaderboard_data)
                yield f"data: {data}\n\n"
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                current_app.logger.error(f"Error in leaderboard stream: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    return Response(stream_with_context(event_stream()), 
                    mimetype="text/event-stream")

# SSE endpoint for real-time leaderboard
@routes_bp.route('/stream/leaderboard')
def stream_leaderboard_route():
    return stream_leaderboard()

# Get leaderboard data
def get_leaderboard_data():
    """Generate leaderboard data with course progress and avatar handling"""
    try:
        # Get all users with their enrollments
        users = User.query.options(
            db.joinedload(User.enrollments)
        ).all()
        
        # Calculate course progress for each user
        user_progress = []
        for user in users:
            total_courses = Course.query.count()
            completed_courses = len([e for e in user.enrollments if e.completed])
            in_progress = len([e for e in user.enrollments if not e.completed and e.completion > 0])
            
            # Calculate overall progress percentage
            total_progress = 0
            for enrollment in user.enrollments:
                total_progress += enrollment.completion if enrollment.completion else 0
            
            avg_progress = (total_progress / len(user.enrollments)) if user.enrollments else 0
            
            user_progress.append({
                'user': user,
                'completed_courses': completed_courses,
                'in_progress_courses': in_progress,
                'total_courses': total_courses,
                'avg_progress': avg_progress,
                'xp': user.xp or 0
            })
        
        # Sort by XP (primary) and then by completed courses (secondary)
        user_progress.sort(key=lambda x: (-x['xp'], -x['completed_courses']))
        
        # Prepare leaderboard data
        leaderboard = []
        for idx, up in enumerate(user_progress[:10], 1):  # Top 10
            user = up['user']
            leaderboard.append({
                'rank': idx,
                'user_id': user.id,
                'username': user.username,
                'xp': up['xp'],
                'avatar': user.avatar or url_for('static', filename='images/default-avatar.png'),
                'courses_completed': up['completed_courses'],
                'courses_in_progress': up['in_progress_courses'],
                'total_courses': up['total_courses'],
                'progress_percentage': round(up['avg_progress'] * 100, 1)
            })
        
        # Add current user's position if not in top 10
        current_user_id = current_user.get_id()
        current_user_data = next((up for up in user_progress if up['user'].id == current_user_id), None)
        
        if current_user_data and not any(u['user_id'] == current_user_id for u in leaderboard):
            user = current_user_data['user']
            current_rank = next((i+1 for i, up in enumerate(user_progress) if up['user'].id == current_user_id), 0)
            
            leaderboard.append({
                'is_current_user': True,
                'rank': current_rank,
                'user_id': user.id,
                'username': user.username,
                'xp': current_user_data['xp'],
                'avatar': user.avatar or url_for('static', filename='images/default-avatar.png'),
                'courses_completed': current_user_data['completed_courses'],
                'courses_in_progress': current_user_data['in_progress_courses'],
                'total_courses': current_user_data['total_courses'],
                'progress_percentage': round(current_user_data['avg_progress'] * 100, 1)
            })
            
        return {
            'leaderboard': leaderboard,
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        current_app.logger.error(f"Error generating leaderboard: {str(e)}")
        return {'error': str(e)}

# Leaderboard route
@routes_bp.route('/leaderboard')
def leaderboard():
    # Get initial leaderboard data for server-side rendering
    leaderboard_data = get_leaderboard_data()
    
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(leaderboard_data)
        
    return render_template(
        'leaderboard.html',
        page_title='Live Leaderboard'
    )

# Chatbot route
@routes_bp.route('/chatbot')
@login_required
def chatbot():
    """Chatbot page route"""
    # Get user's chat history
    chat_history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.timestamp
    ).all()
    
    # Format chat history for template
    messages = []
    for msg in chat_history:
        messages.append({
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_user': msg.is_from_user
        })
    
    # Get user's enrolled courses for context
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_courses = [Course.query.get(e.course_id).title for e in enrollments if Course.query.get(e.course_id)]
    
    return render_template(
        'chatbot.html', 
        chat_history=messages,
        enrolled_courses=enrolled_courses
    )

# Chat API route
@routes_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Chat API for the chatbot"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'status': 'error', 'message': 'No message provided'})
    
    # Save user message
    chat_msg = ChatMessage(
        user_id=current_user.id,
        message=user_message,
        timestamp=datetime.now(),
        is_from_user=True
    )
    db.session.add(chat_msg)
    db.session.commit()
    
    # Get the course context if specified
    course_context = None
    course_title = data.get('course_id')
    if course_title:
        # Find course by title since we're sending title instead of ID from frontend
        course = Course.query.filter_by(title=course_title).first()
        if course:
            course_context = {
                'title': course.title,
                'level': course.level,
                'description': course.description
            }
    
    # Get bot response
    bot_response = get_chatbot_response(current_user.username, user_message, course_context)
    
    # Save bot response
    bot_msg = ChatMessage(
        user_id=current_user.id,
        message=bot_response,
        timestamp=datetime.now(),
        is_from_user=False
    )
    db.session.add(bot_msg)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'response': bot_response,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Route to serve generated certificate files
@routes_bp.route('/certificates/<path:filename>')
def serve_certificate(filename):
    """Serve generated certificate files"""
    try:
        cert_dir = os.path.join(current_app.root_path, 'static', 'generated_certificates')
        filepath = os.path.join(cert_dir, filename)
        
        if not os.path.exists(filepath):
            current_app.logger.error(f"Certificate file not found: {filepath}")
            return "Certificate not found", 404
            
        return send_file(filepath, mimetype='image/jpeg')
    except Exception as e:
        current_app.logger.error(f"Error serving certificate {filename}: {str(e)}")
        return str(e), 500

# Test route for file operations
@routes_bp.route('/test_file_ops')
@login_required
@admin_required
def test_file_operations():
    """Test file operations for certificate generation"""
    try:
        # Test directory creation and file writing
        test_dir = os.path.join(current_app.root_path, 'static', 'test_dir')
        test_file = os.path.join(test_dir, 'test.txt')
        
        # Create test directory
        os.makedirs(test_dir, exist_ok=True, mode=0o777)
        
        # Write test file
        with open(test_file, 'w') as f:
            f.write('Test content')
            
        # Verify file exists
        if not os.path.exists(test_file):
            return f"Failed to create test file at {test_file}"
            
        # Clean up
        try:
            os.remove(test_file)
            os.rmdir(test_dir)
        except Exception as e:
            return f"Cleanup failed: {str(e)}"
            
        return "File operations test completed successfully!"
    except Exception as e:
        return f"Error during file operations test: {str(e)}"

# Certificate Download Route
@routes_bp.route('/download_certificate/<int:course_id>', methods=['GET'])
@login_required
def download_certificate(course_id):
    """
    Generates and serves the course completion certificate for download.
    """
    try:
        # Check if the user is enrolled in the course
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if not enrollment:
            flash('You are not enrolled in this course.', 'danger')
            return redirect(url_for('routes.course_details', course_id=course_id))
        
        # Check if the user has completed the course
        if enrollment.completion < 100:
            flash('You need to complete the course before downloading the certificate.', 'warning')
            return redirect(url_for('routes.course_details', course_id=course_id))
        
        course = Course.query.get_or_404(course_id)
        
        # Check if certificate already exists
        certificate = Certificate.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        # If certificate doesn't exist, create one
        if not certificate:
            try:
                # Generate a unique verification code
                verification_code = str(uuid.uuid4())
                
                # Create certificate record
                certificate = Certificate(
                    user_id=current_user.id,
                    course_id=course_id,
                    issue_date=datetime.utcnow(),
                    verification_code=verification_code,
                    score=enrollment.quiz_attempts.order_by(QuizAttempt.id.desc()).first().score
                )
                
                # Generate the certificate file
                cert_path = generate_certificate(
                    student_name=current_user.username,
                    course_name=course.title,
                    certificate_number=verification_code
                )
                certificate.certificate_url = f"generated_certificates/certificate_{verification_code}.jpg"
                
                db.session.add(certificate)
                db.session.commit()
                print(f"Generated certificate at: {cert_path}")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating certificate: {str(e)}")
                flash('An error occurred while generating your certificate. Please try again.', 'danger')
                return redirect(url_for('routes.course_details', course_id=course_id))
        
        # Generate the certificate file path
        filename = f"certificate_{certificate.verification_code}.jpg"
        
        # Get the static directory path
        static_dir = os.path.join(current_app.root_path, 'static')
        
        # Create the generated_certificates directory if it doesn't exist
        cert_dir = os.path.join(static_dir, 'generated_certificates')
        try:
            os.makedirs(cert_dir, exist_ok=True, mode=0o777)
            print(f"Created/verified certificate directory: {cert_dir}")
        except Exception as e:
            print(f"Error creating certificate directory: {str(e)}")
            raise
            
        filepath = os.path.join(cert_dir, filename)
        
        print(f"Current working directory: {os.getcwd()}")
        print(f"Static directory: {static_dir}")
        print(f"Certificate directory: {cert_dir}")
        print(f"Looking for certificate at: {filepath}")
        print(f"Directory exists: {os.path.exists(cert_dir)}")
        print(f"Is directory: {os.path.isdir(cert_dir)}")
        print(f"Directory permissions: {oct(os.stat(cert_dir).st_mode)[-3:]}")
        
        # If the file doesn't exist, try to generate it
        if not os.path.exists(filepath):
            try:
                print("Certificate file not found, generating a new one...")
                cert_path = generate_certificate(
                    student_name=current_user.username,
                    course_name=course.title,
                    certificate_number=certificate.verification_code
                )
                print(f"Generated certificate at: {cert_path}")
                
                # Verify the file was created
                if not os.path.exists(cert_path):
                    print(f"Error: Certificate file was not created at {cert_path}")
                    raise Exception("Certificate file was not created")
                    
                certificate.certificate_url = f"generated_certificates/certificate_{certificate.verification_code}.jpg"
                db.session.commit()
                print(f"Updated certificate URL in database: {certificate.certificate_url}")
            except Exception as e:
                current_app.logger.error(f"Error generating certificate file: {str(e)}", exc_info=True)
                print(f"Error generating certificate: {str(e)}")
                flash('An error occurred while generating your certificate file. Please try again.', 'danger')
                return redirect(url_for('routes.course_details', course_id=course_id))
        
        # Verify the file exists before trying to send it
        if not os.path.exists(filepath):
            print(f"Error: Certificate file not found at {filepath}")
            flash('Certificate file not found. Please contact support.', 'danger')
            return redirect(url_for('routes.course_details', course_id=course_id))
        
        # Create a safe filename for download
        safe_course_name = "".join(c if c.isalnum() else "_" for c in course.title)
        download_filename = f"Certificate_{safe_course_name}_{current_user.username}.jpg"
        
        # Update the certificate URL in the database if it's not set
        if not certificate.certificate_url or not certificate.certificate_url.startswith('generated_certificates/'):
            certificate.certificate_url = f"generated_certificates/{filename}"
            db.session.commit()
        
        # Return a redirect to the certificate file
        try:
            print(f"Redirecting to certificate URL: /certificates/{filename}")
            return redirect(url_for('routes.serve_certificate', filename=filename))
        except Exception as e:
            print(f"Error redirecting to certificate: {str(e)}")
            raise
        
    except Exception as e:
        current_app.logger.error(f"Error in download_certificate: {str(e)}")
        flash('An error occurred while processing your request. Please try again.', 'danger')
        return redirect(url_for('routes.course_details', course_id=course_id))
    return redirect(url_for('routes.course_details', course_id=course_id))

# User profile route
@routes_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile route. Allows viewing and editing user information."""
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip().lower()
        receive_email_notifications = 'receive_email_notifications' in request.form
        receive_platform_notifications = 'receive_platform_notifications' in request.form

        user_updated = False

        # Validate and update username if changed
        if new_username and new_username != current_user.username:
            if User.query.filter(User.username == new_username, User.id != current_user.id).first():
                flash('Username already taken. Please choose another.', 'danger')
            elif len(new_username) < 3:
                flash('Username must be at least 3 characters long.', 'danger')
            else:
                current_user.username = new_username
                user_updated = True
        
        # Validate and update email if changed
        if new_email and new_email != current_user.email:
            if User.query.filter(User.email == new_email, User.id != current_user.id).first():
                flash('Email address already registered. Please use another.', 'danger')
            # Basic email format check (can be more robust)
            elif '@' not in new_email or '.' not in new_email.split('@')[-1]:
                flash('Invalid email address format.', 'danger')
            else:
                current_user.email = new_email
                user_updated = True

        # Update notification preferences
        if current_user.receive_email_notifications != receive_email_notifications:
            current_user.receive_email_notifications = receive_email_notifications
            user_updated = True
        
        if current_user.receive_platform_notifications != receive_platform_notifications:
            current_user.receive_platform_notifications = receive_platform_notifications
            user_updated = True

        if user_updated:
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error updating profile for user {current_user.id}: {e}")
                flash('Error updating profile. Please try again.', 'danger')
        else:
            # No actual changes were made or validation failed for all attempted changes
            if not any(flash_msg[1] == 'danger' for flash_msg in get_flashed_messages(with_categories=True)):
                 flash('No changes were made to your profile.', 'info')

        return redirect(url_for('routes.profile'))

    # GET request logic remains the same
    user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
    achievements = []
    for ua in user_achievements:
        achievement = Achievement.query.get(ua.achievement_id)
        if achievement:
            achievements.append({
                'title': achievement.title,
                'description': achievement.description,
                'badge_id': achievement.badge_id,
                'earned_date': format_date(ua.earned_date.strftime('%Y-%m-%d'))
            })
    
    # Get user's enrolled courses
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    
    enrolled_courses = []
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            course_data = {
                'id': course.id,
                'title': course.title,
                'image_url': course.image_url,
                'level': course.level,
                'completion': enrollment.completion,
                'instructor': course.instructor,
                'enrollment_date': format_date(enrollment.enrollment_date.strftime('%Y-%m-%d'))
            }
            enrolled_courses.append(course_data)
    
    # Get user's streak
    streak = Streak.query.filter_by(user_id=current_user.id).first()
    streak_data = {
        'current': streak.current_streak if streak else 0,
        'max': streak.max_streak if streak else 0
    }
    
    return render_template(
        'profile.html',
        user=current_user,
        achievements=achievements,
        enrolled_courses=enrolled_courses,
        streak=streak_data
    )

PROFILE_PIC_UPLOAD_FOLDER = 'profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Handles profile picture uploads."""
    if 'profile_picture' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('routes.profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('routes.profile'))

    if file and allowed_file(file.filename):
        # Ensure the upload folder exists
        upload_folder_path = os.path.join(current_app.root_path, 'static', PROFILE_PIC_UPLOAD_FOLDER)
        os.makedirs(upload_folder_path, exist_ok=True)

        # Generate a unique filename to prevent collisions and ensure freshness
        _, file_extension = os.path.splitext(file.filename)
        filename = secure_filename(f"{current_user.id}_{uuid.uuid4().hex}{file_extension}")
        filepath = os.path.join(upload_folder_path, filename)
        
        # Delete old profile picture if it's not the default one
        if current_user.profile_image_url and current_user.profile_image_url != 'default_profile.png':
            old_filepath = os.path.join(upload_folder_path, current_user.profile_image_url)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except OSError as e:
                    logging.error(f"Error deleting old profile picture {old_filepath}: {e}")
                    # Not a critical error, so we can continue

        try:
            file.save(filepath)
            current_user.profile_image_url = filename # Store only the filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving profile picture or updating db for user {current_user.id}: {e}")
            flash('Error updating profile picture. Please try again.', 'danger')
    else:
        flash('Invalid file type. Allowed types are png, jpg, jpeg, gif.', 'danger')
        
    return redirect(url_for('routes.profile'))

@routes_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Handles password change requests."""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if not current_user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
    elif len(new_password) < 8:
        flash('New password must be at least 8 characters long.', 'danger')
    elif new_password != confirm_new_password:
        flash('New passwords do not match.', 'danger')
    elif current_user.check_password(new_password):
        flash('New password cannot be the same as the old password.', 'danger')
    else:
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash('Password updated successfully!', 'success')
            # Consider logging the user out for security or re-authenticating, but for now, just success.
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error changing password for user {current_user.id}: {e}")
            flash('Error updating password. Please try again.', 'danger')
            
    return redirect(url_for('routes.profile'))

# Admin dashboard route
@routes_bp.route('/admin')
@admin_required
def admin():
    """Admin dashboard route"""
    # Get users
    users = User.query.all()
    
    # Get courses
    courses = Course.query.all()
    
    # Get enrollments
    enrollments = db.session.query(
        Course.title, db.func.count(Enrollment.id)
    ).join(
        Course, Course.id == Enrollment.course_id
    ).group_by(
        Course.title
    ).all()
    
    enrollment_data = [{
        'course': course,
        'count': count
    } for course, count in enrollments]
    
    # Get achievements
    achievements = db.session.query(
        Achievement.title, db.func.count(UserAchievement.id)
    ).join(
        Achievement, Achievement.id == UserAchievement.achievement_id
    ).group_by(
        Achievement.title
    ).all()
    
    achievement_data = [{
        'achievement': achievement,
        'count': count
    } for achievement, count in achievements]
    
    return render_template(
        'admin.html',
        users=users,
        courses=courses,
        enrollments=enrollment_data,
        achievements=achievement_data
    )

# Quiz Routes
@routes_bp.route('/course/<int:course_id>/quiz', methods=['GET', 'POST'])
@login_required
def take_quiz(course_id):
    """Handle quiz taking and submission."""
    # Check if user is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not enrollment:
        flash('You must be enrolled in this course to take the quiz.', 'warning')
        return redirect(url_for('routes.course_details', course_id=course_id))
    
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        # Verify CSRF token
        if not request.form.get('csrf_token') == request.cookies.get('csrftoken'):
            abort(400, 'Invalid CSRF token')
        
        # Handle quiz submission
        questions = QuizQuestion.query.filter_by(course_id=course_id).all()
        total_questions = len(questions)
        
        if total_questions == 0:
            flash('No questions found for this quiz.', 'warning')
            return redirect(url_for('routes.course_details', course_id=course_id))
        
        correct_answers = 0
        
        # Debug: Print form data
        print("Form data:", request.form)
        
        for question in questions:
            user_answer = request.form.get(f'question_{question.id}')
            if not user_answer:
                flash('Please answer all questions before submitting.', 'warning')
                return redirect(request.url)
                
            print(f"Question {question.id} - User answer: {user_answer}, Correct answer: {question.correct_answer}")
            if user_answer.strip() == question.correct_answer.strip():
                correct_answers += 1
        
        # Calculate score percentage
        score = round((correct_answers / total_questions) * 100, 2)
        passed = score >= 70  # 70% passing score
        
        try:
            # Debug: Print data before saving
            print(f"Saving quiz attempt - User: {current_user.id}, Course: {course_id}, Score: {score}, Passed: {passed}")
            
            # Save quiz attempt
            attempt = QuizAttempt(
                user_id=current_user.id,
                course_id=course_id,
                score=score,
                passed=passed
            )
            db.session.add(attempt)
            
            # Debug: Print enrollment data
            print(f"Current enrollment completion: {enrollment.completion}")
            
            # Update course progress if passed
            if passed and enrollment.completion < 100:
                enrollment.completion = 100
                print(f"Updated enrollment completion to: {enrollment.completion}")
                
                # Check if this is the first time completing the course
                existing_cert = Certificate.query.filter_by(user_id=current_user.id, course_id=course_id).first()
                print(f"Existing certificate: {existing_cert}")
                
                if not existing_cert:
                    try:
                        # Generate certificate
                        verification_code = str(uuid.uuid4())
                        print(f"Generating new certificate with verification code: {verification_code}")
                        
                        certificate = Certificate(
                            user_id=current_user.id,
                            course_id=course_id,
                            issue_date=datetime.utcnow(),
                            verification_code=verification_code,
                            score=score
                        )
                        db.session.add(certificate)
                        
                        # Generate certificate file
                        print("Generating certificate file...")
                        generate_certificate(current_user, course, verification_code)
                        print("Certificate file generated successfully")
                        
                        # Update certificate URL
                        certificate.certificate_url = f"generated_certificates/certificate_{verification_code}.jpg"
                        
                    except Exception as cert_error:
                        print(f"Error generating certificate: {str(cert_error)}")
                        raise
            
            # Commit all changes
            db.session.commit()
            print("Database changes committed successfully")
            
            return render_template('quiz_result.html', 
                               course=course, 
                               score=score, 
                               passed=passed,
                               total_questions=total_questions,
                               correct_answers=correct_answers)
                               
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = traceback.format_exc()
            print(f"Error saving quiz attempt: {str(e)}\n{error_details}")
            flash(f'An error occurred while processing your quiz: {str(e)}', 'danger')
            return redirect(request.url)
    
    # GET request - show quiz
    questions = QuizQuestion.query.filter_by(course_id=course_id).all()
    
    if not questions:
        flash('No quiz questions available for this course yet.', 'info')
        return redirect(url_for('routes.course_details', course_id=course_id))
    
    return render_template('take_quiz.html', course=course, questions=questions)

# Error handlers
@routes_bp.app_errorhandler(404)
def page_not_found(e):
    """404 page not found handler"""
    return render_template('404.html'), 404

@routes_bp.app_errorhandler(500)
def server_error(e):
    """500 server error handler"""
    logging.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500