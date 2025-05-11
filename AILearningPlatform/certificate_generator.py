from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import os
import logging
from datetime import datetime
import textwrap

def generate_certificate(student_name, course_name, certificate_number):
    try:
        print(f"Starting certificate generation for {student_name} - {course_name}")
        
        # Get the directory of the current script (AILearningPlatform/certificate_generator.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define paths for assets and output
        assets_folder = os.path.join(script_dir, 'static', 'assets', 'certificates')
        output_folder = os.path.join(script_dir, 'static', 'generated_certificates')
        
        # Ensure folders exist with full permissions
        try:
            os.makedirs(assets_folder, mode=0o777, exist_ok=True)
            os.makedirs(output_folder, mode=0o777, exist_ok=True)
            print(f"Created/verified directories: {assets_folder} and {output_folder}")
        except Exception as e:
            print(f"Error creating directories: {str(e)}")
            raise
        
        # Current date for the certificate
        date = datetime.now().strftime("%B %d, %Y")
        print(f"Certificate date: {date}")

        # Create a new image with a white background
        width, height = 2000, 1414
        template = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(template)
        
        # Add a decorative border
        border_color = (70, 130, 180)  # Steel blue
        draw.rectangle([(50, 50), (width-50, height-50)], outline=border_color, width=10)
        
        # Add a decorative element (a simple line under the title)
        draw.line([(width//4, 450), (3*width//4, 450)], fill=border_color, width=5)
        
        # Try to load fonts, fall back to default if not available
        try:
            # Try to use system fonts
            title_font = ImageFont.truetype("arial.ttf", 80)
            name_font = ImageFont.truetype("arial.ttf", 70)
            text_font = ImageFont.truetype("arial.ttf", 50)
            small_font = ImageFont.truetype("arial.ttf", 30)
        except:
            # Fall back to default font if Arial is not available
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Define positions
        title_y = 350
        cert_y = 500
        name_y = 650
        complete_y = 750
        course_y = 850
        date_y = 950
        
        # Draw title
        title = "CERTIFICATE OF COMPLETION"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, title_y), title, font=title_font, fill=border_color)
        
        # Draw "This is to certify that"
        cert_text = "This is to certify that"
        cert_bbox = draw.textbbox((0, 0), cert_text, font=text_font)
        cert_width = cert_bbox[2] - cert_bbox[0]
        cert_x = (width - cert_width) // 2
        draw.text((cert_x, cert_y), cert_text, font=text_font, fill="black")
        
        # Draw student name with a highlight
        name_text = f"{student_name}"
        name_bbox = draw.textbbox((0, 0), name_text, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (width - name_width) // 2
        
        # Add a highlight behind the name
        padding = 20
        draw.rectangle(
            [name_x - padding, name_y - padding, 
             name_x + name_width + padding, name_y + (name_bbox[3] - name_bbox[1]) + padding],
            fill=(240, 248, 255)  # AliceBlue
        )
        draw.text((name_x, name_y), name_text, font=name_font, fill=border_color)
        
        # Draw "has successfully completed"
        complete_text = "has successfully completed the course"
        complete_bbox = draw.textbbox((0, 0), complete_text, font=text_font)
        complete_width = complete_bbox[2] - complete_bbox[0]
        complete_x = (width - complete_width) // 2
        draw.text((complete_x, complete_y), complete_text, font=text_font, fill="black")
        
        # Draw course name
        course_bbox = draw.textbbox((0, 0), course_name, font=text_font)
        course_width = course_bbox[2] - course_bbox[0]
        course_x = (width - course_width) // 2
        draw.text((course_x, course_y + 100), course_name, font=text_font, fill=border_color)
        
        # Draw date
        date_text = f"on {date}"
        date_bbox = draw.textbbox((0, 0), date_text, font=text_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_x = (width - date_width) // 2
        draw.text((date_x, date_y + 150), date_text, font=text_font, fill="black")
        
        # Add certificate number
        cert_num_text = f"Certificate ID: {certificate_number}"
        draw.text((width - 600, height - 100), cert_num_text, font=small_font, fill="gray")
        
        # Save the certificate with a unique filename
        filename = f"certificate_{certificate_number}.jpg"
        output_path = os.path.join(output_folder, filename)
        
        try:
            # Ensure the directory exists with proper permissions
            os.makedirs(os.path.dirname(output_path), exist_ok=True, mode=0o777)
            
            # Save the image with high quality
            temp_path = f"{output_path}.tmp"
            template.save(temp_path, "JPEG", quality=90, optimize=True, progressive=True)
            
            # On Windows, we need to remove the destination file if it exists
            if os.path.exists(output_path):
                os.remove(output_path)
                
            # Rename the temp file to the final filename
            os.rename(temp_path, output_path)
            
            # Set file permissions (readable by all)
            try:
                os.chmod(output_path, 0o666)  # rw-rw-rw-
            except Exception as perm_error:
                print(f"Warning: Could not set file permissions: {str(perm_error)}")
            
            print(f"Certificate saved to: {output_path}")
            
            # Verify the file was created
            if not os.path.exists(output_path):
                raise Exception(f"Failed to save certificate to {output_path}")
                
            return output_path
            
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
            print(f"Error saving certificate: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Output folder: {output_folder}")
            print(f"Output path: {output_path}")
            print(f"Directory exists: {os.path.exists(os.path.dirname(output_path))}")
            if os.path.exists(os.path.dirname(output_path)):
                print(f"Directory permissions: {oct(os.stat(os.path.dirname(output_path)).st_mode)[-3:]}")
            raise
        
    except Exception as e:
        error_msg = f"Error generating certificate for {student_name} in {course_name}: {str(e)}"
        print(error_msg)
        logging.error(error_msg, exc_info=True)
        
        # Try to return a path to prevent the app from crashing
        try:
            output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'generated_certificates')
            os.makedirs(output_folder, exist_ok=True, mode=0o777)
            return os.path.join(output_folder, f"certificate_{certificate_number}.jpg")
        except Exception as inner_e:
            print(f"Failed to create error path: {str(inner_e)}")
            raise Exception(f"Certificate generation failed: {str(e)}") from e
