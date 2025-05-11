"""
Certificate Blueprint

This module handles all certificate-related routes and functionality.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Certificate, Course, User
from extensions import db
import os
from datetime import datetime

# Create blueprint
cert_bp = Blueprint('certificate', __name__)

@cert_bp.route('/my-certificates')
@login_required
def my_certificates():
    """Display all certificates for the current user."""
    try:
        # Get all certificates for the current user with course details
        certificates = db.session.query(
            Certificate, 
            Course
        ).join(
            Course, 
            Certificate.course_id == Course.id
        ).filter(
            Certificate.user_id == current_user.id
        ).order_by(
            Certificate.issue_date.desc()
        ).all()
        
        return render_template(
            'certificates/my_certificates.html',
            certificates=certificates,
            title='My Certificates'
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching certificates: {e}")
        flash('An error occurred while fetching your certificates. Please try again later.', 'error')
        return redirect(url_for('routes.index'))

@cert_bp.route('/download/<int:certificate_id>')
@login_required
def download_certificate(certificate_id):
    """Download a certificate as PDF."""
    try:
        certificate = Certificate.query.get_or_404(certificate_id)
        
        # Check if the current user is the owner or an admin
        if current_user.id != certificate.user_id and not current_user.is_admin:
            abort(403)
        
        # Check if the certificate file exists
        if not certificate.certificate_url or not os.path.exists(certificate.certificate_url):
            # Try to regenerate the certificate
            if not certificate.generate_pdf():
                flash('Certificate file not found and could not be regenerated.', 'error')
                return redirect(url_for('certificate.my_certificates'))
        
        # Get the directory and filename from the certificate URL
        directory = os.path.dirname(certificate.certificate_url)
        filename = os.path.basename(certificate.certificate_url)
        
        # Create a nice filename for download
        course_title = certificate.course.title.replace(' ', '_')
        download_filename = f"Certificate_{course_title}_{certificate.verification_code}.pdf"
        
        # Serve the file for download
        return send_file(
            os.path.join(current_app.root_path, 'static', directory, filename),
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f"Error downloading certificate {certificate_id}: {e}")
        flash('An error occurred while downloading the certificate. Please try again later.', 'error')
        return redirect(url_for('certificate.my_certificates'))

@cert_bp.route('/verify', methods=['GET'])
def verify():
    """Verify a certificate using a verification code."""
    code = request.args.get('code')
    
    if not code:
        return render_template('certificates/verify.html', certificate=None)
    
    try:
        # Find certificate by verification code
        certificate = Certificate.query.filter_by(verification_code=code).first()
        
        if not certificate:
            return render_template(
                'certificates/verify.html',
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
                    'certificates/verify.html',
                    certificate=None,
                    error='Error generating certificate. Please contact support.'
                )
        
        return render_template(
            'certificates/verify.html', 
            certificate=certificate,
            title='Certificate Verification'
        )
    
    except Exception as e:
        current_app.logger.error(f"Error during certificate verification: {e}")
        return render_template(
            'certificates/verify.html',
            certificate=None,
            error='An error occurred while verifying the certificate. Please try again later.'
        ), 500

# Error handlers for certificate routes
@cert_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@cert_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@cert_bp.app_errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
