from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, mail, limiter
from models import User, Course, Enrollment, Certificate
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime, timedelta
import secrets
import os
from flask_mail import Message
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')

def verify_token(token, expiration=86400):  # 24 hours expiration
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token, salt='email-verification-salt', max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
    return email

def send_verification_email(user):
    token = generate_verification_token(user.email)
    user.email_verification_token = token
    user.email_verification_sent_at = datetime.utcnow()
    db.session.commit()
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg = Message('Verify Your Email - Learnify',
                  recipients=[user.email])
    msg.body = f'''To verify your email, visit the following link:
{verification_url}

If you did not make this request, please ignore this email.
'''
    
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {e}")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))
            
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            email_verified=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    if current_user.is_authenticated and current_user.email_verified:
        return redirect(url_for('main.index'))
    
    email = verify_token(token)
    if not email:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.register'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user account.', 'danger')
        return redirect(url_for('auth.register'))
    
    if user.email_verified:
        flash('Email already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.email_verified:
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=remember)
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-certificate', methods=['GET'])
def verify_certificate():
    """Verify a certificate using a verification code."""
    code = request.args.get('code')
    
    if not code:
        return render_template('verify_certificate.html', certificate=None)
    
    try:
        # Find certificate by verification code
        certificate = Certificate.query.filter_by(verification_code=code).first()
        
        if not certificate:
            return render_template(
                'verify_certificate.html',
                certificate=None,
                error='Invalid verification code. Please check and try again.'
            )
        
        # If certificate URL doesn't exist, generate the PDF
        if not certificate.certificate_url or not os.path.exists(certificate.certificate_url):
            try:
                certificate.generate_pdf()
            except Exception as e:
                current_app.logger.error(f"Error generating certificate PDF: {e}")
                return render_template(
                    'verify_certificate.html',
                    certificate=None,
                    error='Error generating certificate. Please contact support.'
                )
        
        return render_template('verify_certificate.html', certificate=certificate)
    
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error during certificate verification: {e}")
        return render_template(
            'verify_certificate.html',
            certificate=None,
            error='An error occurred while verifying the certificate. Please try again later.'
        ), 500


@auth_bp.route('/certificate/<int:certificate_id>')
@limiter.limit("10 per minute")
def view_certificate(certificate_id):
    """View a certificate by ID."""
    try:
        certificate = Certificate.query.get_or_404(certificate_id)
        
        # Only allow viewing if the certificate exists and has a valid URL
        if not certificate or not certificate.certificate_url:
            abort(404)
            
        # Check if the current user is the owner or an admin
        if not current_user.is_authenticated or (current_user.id != certificate.user_id and not current_user.is_admin):
            abort(403)
            
        # Get the directory and filename from the certificate URL
        directory = os.path.dirname(certificate.certificate_url)
        filename = os.path.basename(certificate.certificate_url)
        
        # Serve the file from the static directory
        return send_from_directory(
            directory=os.path.join(current_app.root_path, 'static', directory),
            path=filename,
            as_attachment=False
        )
    except Exception as e:
        current_app.logger.error(f"Error serving certificate {certificate_id}: {e}")
        abort(404)


def send_certificate_email(certificate):
    """Helper function to send certificate email."""
    try:
        certificate.send_certificate_email()
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending certificate email: {e}")
        return False

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.email_verified:
            flash('Please verify your email to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
