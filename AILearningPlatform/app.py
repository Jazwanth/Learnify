import os
import logging
import os
import logging
from flask import Flask, render_template
from flask_login import current_user

# Import extensions from the new extensions.py file
from extensions import db, login_manager, csrf, mail, limiter, migrate

# Import blueprints
from auth import auth_bp
from certificate import cert_bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Import models, routes, and database utilities at the global scope.
# These will now use 'db' from 'extensions.py'
from models import User, Course, Module, Quiz, Enrollment, Progress, Achievement, UserAchievement, Streak, Certificate
from routes import routes_bp
from database import init_sample_data

def create_app(config=None):
    """Factory function to create and configure the Flask application"""
    app = Flask(__name__)
    
    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get("SESSION_SECRET", "dev_secret_key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///learnify.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_recycle": 300,
            "pool_pre_ping": True,
        },
        # Flask-Mail configuration
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1'],
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1'],
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME', ''),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD', ''),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@learnify.com'),
        # Rate limiting
        RATELIMIT_DEFAULT='200 per day;50 per hour'
    )
    
    # Override with any custom config
    if config:
        app.config.update(config)
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Initialize Flask-Migrate after db is initialized
    migrate.init_app(app, db, render_as_batch=True)
    
    # Register blueprints
    app.register_blueprint(routes_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cert_bp, url_prefix='/certificate')
    
    # Register a shell context processor
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Course': Course,
            'Module': Module,
            'Quiz': Quiz,
            'Enrollment': Enrollment,
            'Progress': Progress,
            'Achievement': Achievement,
            'UserAchievement': UserAchievement,
            'Streak': Streak,
            'Certificate': Certificate
        }
    
    # Create database tables and initialize data within an app context
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Initialize sample data
        init_sample_data(app)
        
        # Create admin user if it doesn't exist
        # Authentication routes have been moved to auth.py
        
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Context processor to make current_user available in all templates
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
            
    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def init_db():
    """
    Initialize the database with sample data.
    This is useful for development and testing.
    """
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Initialize sample data
        from database import init_sample_data
        init_sample_data(app)
        
        print("Database initialized with sample data!")

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
