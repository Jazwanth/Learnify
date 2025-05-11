"""
Certificate generation and management utilities for Learnify.
"""
import os
from datetime import datetime
from extensions import db
from models import Certificate, Enrollment

def generate_certificate(user_id, course_id, score):
    """
    Generate a certificate for a user who has completed a course.
    
    Args:
        user_id (int): ID of the user
        course_id (int): ID of the course
        score (float): Final score/percentage achieved in the course
        
    Returns:
        Certificate: The created certificate object, or None if creation failed
    """
    try:
        # Check if certificate already exists
        existing_cert = Certificate.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
        
        if existing_cert:
            # Update existing certificate if score is higher
            if score > existing_cert.score:
                existing_cert.score = score
                existing_cert.issue_date = datetime.utcnow()
                db.session.commit()
                
                # Regenerate PDF with updated score
                existing_cert.generate_pdf()
                
                # Resend email with updated certificate
                from auth import send_certificate_email
                send_certificate_email(existing_cert)
                
            return existing_cert
        
        # Create new certificate
        certificate = Certificate(
            user_id=user_id,
            course_id=course_id,
            score=score,
            issue_date=datetime.utcnow()
        )
        
        db.session.add(certificate)
        db.session.flush()  # Get the certificate ID before commit
        
        # Generate PDF
        certificate.generate_pdf()
        
        db.session.commit()
        
        # Send email with certificate
        from auth import send_certificate_email
        send_certificate_email(certificate)
        
        return certificate
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f"Error generating certificate: {e}")
        return None

def check_and_issue_certificate(user_id, course_id):
    """
    Check if a user has completed a course and issue a certificate if they have.
    
    Args:
        user_id (int): ID of the user
        course_id (int): ID of the course
        
    Returns:
        Certificate: The created or updated certificate, or None if not eligible
    """
    try:
        # Get the enrollment
        enrollment = Enrollment.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
        
        if not enrollment or enrollment.completion < 100.0:
            return None
            
        # Check if all modules are completed with passing scores
        from models import Progress, Module
        
        modules = Module.query.filter_by(course_id=course_id).all()
        if not modules:
            return None
            
        # Calculate average score across all module quizzes
        total_score = 0
        module_count = 0
        
        for module in modules:
            progress = Progress.query.filter_by(
                user_id=user_id,
                module_id=module.id
            ).first()
            
            if not progress or not progress.quiz_score:
                return None  # Missing progress or quiz score for a module
                
            total_score += progress.quiz_score
            module_count += 1
        
        if module_count == 0:
            return None
            
        average_score = total_score / module_count
        
        # Only issue certificate if average score is 70% or higher
        if average_score >= 70.0:
            return generate_certificate(user_id, course_id, average_score)
            
        return None
        
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error checking certificate eligibility: {e}")
        return None
