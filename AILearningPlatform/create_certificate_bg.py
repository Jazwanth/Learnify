"""
Script to create a certificate background image.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_certificate_background():
    # Create a new image with a white background (A4 size in pixels at 72 DPI)
    width, height = 842, 595  # A4 landscape at 72 DPI (11.69 x 8.27 in)
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Add a border
    border_width = 20
    draw.rectangle(
        [(border_width, border_width), 
         (width - border_width, height - border_width)],
        outline='#4e73df',
        width=5
    )
    
    # Add a decorative border
    border_inner = 40
    draw.rectangle(
        [(border_inner, border_inner), 
         (width - border_inner, height - border_inner)],
        outline='#4e73df',
        width=1
    )
    
    # Add a decorative element in the corners
    corner_size = 100
    line_width = 3
    
    # Top-left corner
    draw.line([(border_inner, border_inner + corner_size), 
               (border_inner, border_inner), 
               (border_inner + corner_size, border_inner)], 
              fill='#4e73df', width=line_width)
    
    # Top-right corner
    draw.line([(width - border_inner - corner_size, border_inner), 
               (width - border_inner, border_inner), 
               (width - border_inner, border_inner + corner_size)], 
              fill='#4e73df', width=line_width)
    
    # Bottom-left corner
    draw.line([(border_inner, height - border_inner - corner_size), 
               (border_inner, height - border_inner), 
               (border_inner + corner_size, height - border_inner)], 
              fill='#4e73df', width=line_width)
    
    # Bottom-right corner
    draw.line([(width - border_inner - corner_size, height - border_inner), 
               (width - border_inner, height - border_inner), 
               (width - border_inner, height - border_inner - corner_size)], 
              fill='#4e73df', width=line_width)
    
    # Add a watermark
    try:
        # Try to load a nice font if available
        font_path = os.path.join('static', 'fonts', 'GreatVibes-Regular.ttf')
        font = ImageFont.truetype(font_path, 40)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add a watermark text
    watermark = "Learnify - Empowering Education"
    text_bbox = draw.textbbox((0, 0), watermark, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Position the watermark in the center
    x = (width - text_width) // 2
    y = height - 80
    
    # Draw semi-transparent watermark
    watermark_image = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
    watermark_draw = ImageDraw.Draw(watermark_image)
    watermark_draw.text((0, 0), watermark, fill=(78, 115, 223, 64), font=font)
    
    # Rotate the watermark
    watermark_image = watermark_image.rotate(30, expand=1)
    
    # Paste the watermark multiple times
    for i in range(-2, 3):
        for j in range(-1, 2):
            image.paste(
                watermark_image, 
                (x + i * 200 - text_width//2, y + j * 200 - text_height//2), 
                watermark_image
            )
    
    # Save the image
    os.makedirs('static/images', exist_ok=True)
    output_path = os.path.join('static', 'images', 'certificate_bg.jpg')
    image.save(output_path, 'JPEG', quality=90)
    print(f"Certificate background created at: {output_path}")
    return output_path

if __name__ == "__main__":
    create_certificate_background()
