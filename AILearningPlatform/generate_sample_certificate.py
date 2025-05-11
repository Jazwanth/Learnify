"""
Script to generate a sample certificate for testing.
"""
import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Course, Certificate

def create_sample_certificate():
    """Create a sample certificate for testing."""
    app = create_app()
    
    with app.app_context():
        # Create a test user if not exists
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password='testpassword',  # Will be hashed
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            print("Created test user:", user.username)
        
        # Create a test course if not exists
        course = Course.query.filter_by(title='Sample Course').first()
        if not course:
            course = Course(
                title='Sample Course',
                description='A sample course for testing certificate generation',
                instructor='Test Instructor',
                duration=30,
                level='Beginner',
                category='Testing',
                image_url='images/sample.jpg',
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            print("Created test course:", course.title)
        
        # Generate a certificate
        from certificate_utils import generate_certificate
        certificate = generate_certificate(user.id, course.id, 92.5)
        
        if certificate:
            print("\nCertificate generated successfully!")
            print(f"Certificate ID: {certificate.id}")
            print(f"User: {user.username}")
            print(f"Course: {course.title}")
            print(f"Score: {certificate.score}%")
            print(f"Verification Code: {certificate.verification_code}")
            print(f"Certificate URL: {certificate.certificate_url}")
            
            # Verify the certificate file exists
            if os.path.exists(certificate.certificate_url):
                print("\nCertificate PDF was created successfully!")
                print(f"File size: {os.path.getsize(certificate.certificate_url) / 1024:.2f} KB")
                print(f"File path: {os.path.abspath(certificate.certificate_url)}")
            else:
                print("\nError: Certificate file was not created!")
                print("Expected path:", os.path.abspath(certificate.certificate_url))
        else:
            print("\nError: Failed to generate certificate!")

if __name__ == "__main__":
    print("=== Generating Sample Certificate ===\n")
    create_sample_certificate()
    print("\nTest completed!")
