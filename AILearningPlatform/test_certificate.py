"""
Script to test certificate generation.
"""
import os
import sys
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Course, Certificate

app = create_app()

def create_test_data():
    """Create test user and course for certificate testing."""
    with app.app_context():
        # Create test user if not exists
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password='testpassword',
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created test user: {user.username}")
        
        # Create test course if not exists
        course = Course.query.filter_by(title='Test Course').first()
        if not course:
            course = Course(
                title='Test Course',
                description='A test course for certificate generation',
                instructor='Test Instructor',
                duration=30,
                level='Beginner',
                category='Testing',
                image_url='images/test.jpg',
                created_at=datetime.utcnow()
            )
            db.session.add(course)
            db.session.commit()
            print(f"Created test course: {course.title}")
        
        return user, course

def test_certificate_generation():
    """Test certificate generation and email sending."""
    with app.app_context():
        # Create test data
        user, course = create_test_data()
        
        # Generate a certificate
        from certificate_utils import generate_certificate
        certificate = generate_certificate(user.id, course.id, 95.5)
        
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
            else:
                print("\nError: Certificate file was not created!")
        else:
            print("\nError: Failed to generate certificate!")

if __name__ == "__main__":
    print("=== Testing Certificate Generation ===\n")
    test_certificate_generation()
    print("\nTest completed!")
