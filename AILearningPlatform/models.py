"""
Models for the e-learning platform.

This module defines the SQLAlchemy models for the application.
"""
import datetime
import json
from extensions import db
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """User model for the e-learning platform."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), default='student')
    joined_date = Column(DateTime, default=datetime.datetime.utcnow)
    profile_image_url = Column(String(255), default='default_profile.png') # Added profile image URL

    # Notification Preferences
    receive_email_notifications = Column(Boolean, default=True, nullable=False)
    receive_platform_notifications = Column(Boolean, default=True, nullable=False)
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(100), unique=True, nullable=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    
    # Relationships with explicit back_populates
    enrollments = relationship('Enrollment', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    achievements = relationship('UserAchievement', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    progress = relationship('Progress', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    streak = relationship('Streak', back_populates='user', uselist=False, cascade='all, delete-orphan')
    chat_messages = relationship('ChatMessage', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    certificates = relationship('Certificate', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    quiz_attempts = relationship('QuizAttempt', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_id(self):
        return str(self.id)
        
    @property
    def is_active(self):
        """Check if the user is active."""
        return True
        
    @property
    def is_authenticated(self):
        """Check if the user is authenticated."""
        return True
        
    @property
    def is_anonymous(self):
        """Check if the user is anonymous."""
        return False
        
    def get_security_payload(self):
        """Return data for token generation."""
        return {
            'user_id': self.id,
            'email': self.email,
            'username': self.username
        }
        
    def has_enrolled_in_course(self, course_id):
        """Check if user is enrolled in a specific course."""
        return bool(Enrollment.query.filter_by(
            user_id=self.id, course_id=course_id
        ).first())
        
    def get_enrolled_courses(self):
        """Get all courses the user is enrolled in."""
        return Course.query.join(Enrollment).filter(
            Enrollment.user_id == self.id
        ).all()
        
    def get_completed_courses(self):
        """Get all courses the user has completed."""
        return Course.query.join(Enrollment).filter(
            Enrollment.user_id == self.id,
            Enrollment.completion == 100.0
        ).all()
        
    def get_certificates(self):
        """Get all certificates earned by the user."""
        return Certificate.query.filter_by(user_id=self.id).all()
    
    @property
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == 'admin'
        
    def __repr__(self):
        return f'<User {self.username}>'


class Course(db.Model):
    """Course model for the e-learning platform."""
    __tablename__ = 'courses'
    
    # Relationships with explicit back_populates
    certificates = relationship('Certificate', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(200))
    instructor = Column(String(100))
    duration = Column(String(50))
    level = Column(String(20))
    
    # Relationships with explicit back_populates
    modules = relationship('Module', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = relationship('Enrollment', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    quiz_questions = relationship('QuizQuestion', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    quiz_attempts = relationship('QuizAttempt', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'


class Module(db.Model):
    """Module model for courses."""
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    video_url = Column(String(200))
    order = Column(Integer, default=0)
    
    # Relationships
    quiz = relationship('Quiz', back_populates='module', lazy='dynamic', cascade='all, delete-orphan')
    progress = relationship('Progress', back_populates='module', lazy='dynamic', cascade='all, delete-orphan')
    course = relationship('Course', back_populates='modules')
    
    def __repr__(self):
        return f'<Module {self.title}>'


class Quiz(db.Model):
    """Quiz model for course modules."""
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    question = Column(Text, nullable=False)
    _options = Column(Text, nullable=False)
    answer = Column(String(200), nullable=False)
    
    # Relationships
    module = relationship('Module', back_populates='quiz')
    
    @property
    def options(self):
        return json.loads(self._options)
        
    @options.setter
    def options(self, options_list):
        self._options = json.dumps(options_list)
    
    def __repr__(self):
        return f'<Quiz {self.id} for module {self.module_id}>'


class QuizQuestion(db.Model):
    """Quiz question model for courses."""
    __tablename__ = 'quiz_questions'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    question = Column(String(500), nullable=False)
    options = Column(JSON, nullable=False)  # List of options
    correct_answer = Column(String(500), nullable=False)  # The correct answer
    
    # Relationship
    course = relationship('Course', back_populates='quiz_questions')
    
    def __repr__(self):
        return f'<QuizQuestion {self.id} for course {self.course_id}>'


class QuizAttempt(db.Model):
    """Tracks user quiz attempts and scores."""
    __tablename__ = 'quiz_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    score = Column(Float, nullable=False)  # Percentage score
    passed = Column(Boolean, default=False)
    attempt_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='quiz_attempts')
    course = relationship('Course', back_populates='quiz_attempts')
    
    def __repr__(self):
        return f'<QuizAttempt {self.id} by user {self.user_id} for course {self.course_id}>'


class Enrollment(db.Model):
    """Enrollment model linking users to courses."""
    __tablename__ = 'enrollments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    enrollment_date = Column(DateTime, default=datetime.datetime.utcnow)
    completion = Column(Float, default=0.0)
    last_module = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')
    
    def __repr__(self):
        return f'<Enrollment user_id={self.user_id} course_id={self.course_id}>'


class Progress(db.Model):
    """Progress model to track user progress in courses."""
    __tablename__ = 'progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    completion = Column(Float, default=0.0)
    quiz_score = Column(Integer)
    last_updated = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc))
    
    # Relationships
    user = relationship('User', back_populates='progress')
    course = relationship('Course')
    module = relationship('Module', back_populates='progress')
    
    def __repr__(self):
        return f'<Progress user_id={self.user_id} module_id={self.module_id} completion={self.completion}>'


class Achievement(db.Model):
    """Achievement model for user badges."""
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    image_url = Column(String(200))
    badge_id = Column(String(50))  # SVG ID for badge
    
    # Relationships with explicit back_populates
    users = relationship('UserAchievement', back_populates='achievement', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Achievement {self.title}>'


class UserAchievement(db.Model):
    """User Achievement model linking users to achievements."""
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=False)
    earned_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='achievements')
    achievement = relationship('Achievement', back_populates='users')
    
    def __repr__(self):
        return f'<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id}>'


class Streak(db.Model):
    """User streak model for tracking consecutive days."""
    __tablename__ = 'streaks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='streak')
    
    def __repr__(self):
        return f'<Streak user_id={self.user_id} current={self.current_streak} max={self.max_streak}>'


class Certificate(db.Model):
    """Certificate model for course completion certificates."""
    __tablename__ = 'certificates'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', name='fk_certificate_user'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE', name='fk_certificate_course'), nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    score = Column(Float, nullable=False)
    certificate_url = Column(String(255), nullable=True)
    verification_code = Column(String(50), unique=True, nullable=True)
    
    # Relationships with explicit back_populates
    user = relationship('User', back_populates='certificates')
    course = relationship('Course', back_populates='certificates')
    
    def generate_verification_code(self):
        """Generate a unique verification code for this certificate."""
        import uuid
        self.verification_code = str(uuid.uuid4())
        return self.verification_code
    
    def verify_certificate(self, code):
        """Verify the certificate using the verification code."""
        return self.verification_code == code
    
    def generate_pdf(self, output_path=None):
        """Generate a PDF certificate."""
        from fpdf import FPDF
        import os
        
        # Create PDF
        pdf = FPDF(orientation='L')
        pdf.add_page()
        
        # Add background
        pdf.image('static/images/certificate_bg.jpg', 0, 0, 297, 210)  # A4 landscape
        
        # Add content
        pdf.set_font('Arial', 'B', 24)
        pdf.set_text_color(0, 0, 0)
        
        # Title
        pdf.cell(0, 40, '', 0, 1)
        pdf.cell(0, 20, 'CERTIFICATE OF COMPLETION', 0, 1, 'C')
        
        # Subtitle
        pdf.set_font('Arial', 'I', 16)
        pdf.cell(0, 25, 'This is to certify that', 0, 1, 'C')
        
        # User name
        pdf.set_font('Arial', 'B', 28)
        pdf.cell(0, 30, self.user.username, 0, 1, 'C')
        
        # Course name
        pdf.set_font('Arial', 'I', 16)
        pdf.cell(0, 20, 'has successfully completed the course', 0, 1, 'C')
        
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 20, f'"{self.course.title}"', 0, 1, 'C')
        
        # Score and date
        pdf.set_font('Arial', '', 14)
        pdf.cell(0, 20, f'with a score of {self.score}%', 0, 1, 'C')
        
        # Issue date
        pdf.set_font('Arial', 'I', 12)
        pdf.cell(0, 20, f'Issued on {self.issue_date.strftime("%B %d, %Y")}', 0, 1, 'C')
        
        # Verification code
        if not self.verification_code:
            self.generate_verification_code()
            db.session.commit()
            
        pdf.set_text_color(128, 128, 128)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Verification Code: {self.verification_code}', 0, 1, 'C')
        
        # Save the PDF
        if not output_path:
            os.makedirs('static/certificates', exist_ok=True)
            output_path = f'static/certificates/certificate_{self.id}.pdf'
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        pdf.output(output_path, 'F')
        self.certificate_url = output_path
        db.session.commit()
        
        return output_path
    
    def send_certificate_email(self):
        """Send the certificate to the user's email."""
        from flask import current_app, render_template, url_for
        from flask_mail import Message
        from extensions import mail
        
        # Generate PDF if not already generated
        if not self.certificate_url or not os.path.exists(self.certificate_url):
            self.generate_pdf()
        
        # Prepare email
        subject = f'Your Certificate for {self.course.title} - Learnify'
        
        # Render email template
        html_body = render_template(
            'emails/certificate_email.html',
            user=self.user,
            course=self.course,
            certificate=self,
            verification_url=url_for('verify_certificate', code=self.verification_code, _external=True)
        )
        
        # Create message
        msg = Message(
            subject=subject,
            recipients=[self.user.email],
            html=html_body
        )
        
        # Attach certificate
        with current_app.open_resource(self.certificate_url) as fp:
            msg.attach(
                f'Certificate_{self.course.title.replace(" ", "_")}.pdf',
                'application/pdf',
                fp.read()
            )
        
        # Send email
        mail.send(msg)
    
    def __repr__(self):
        return f'<Certificate {self.id} for user {self.user_id} in course {self.course_id}>'


class ChatMessage(db.Model):
    """Chat message model for chatbot conversations."""
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE', name='fk_chatmessage_user'), nullable=False)
    message = Column(Text, nullable=False)
    is_from_user = Column(Boolean, default=True, nullable=False)  # True if from user, False if from bot
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='chat_messages')
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_from_user': self.is_from_user,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.id} from user {self.user_id}>'
