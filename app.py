from flask import Flask, render_template, request, jsonify
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
import base64
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, GappedSquareModuleDrawer,
    HorizontalBarsDrawer, VerticalBarsDrawer, CircleModuleDrawer
)
from qrcode.image.styledpil import StyledPilImage
import os

app = Flask(__name__)

# Theme to module drawer mapping
THEME_DRAWERS = {
    'rounded': RoundedModuleDrawer(),
    'gapped': GappedSquareModuleDrawer(),
    'horizontal': HorizontalBarsDrawer(),
    'vertical': VerticalBarsDrawer(),
    'circle': CircleModuleDrawer()
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_qr():
    try:
        # Form data processing
        data = request.form.get('qrdata', '')
        if not data:
            raise ValueError("Please enter text or URL for the QR code")
            
        fg_color = request.form.get('fg', '#000000')
        bg_color = request.form.get('bg', '#ffffff')
        color_type = request.form.get('colortype', 'solid')
        inverse = request.form.get('inverse') == 'on'
        title = request.form.get('title', '')
        theme = request.form.get('theme', 'rounded')
        border = request.form.get('border', 'none')
        size = max(100, min(int(request.form.get('size', 300)), 1000))

        # Color handling
        if inverse:
            fg_color, bg_color = get_effective_colors(fg_color, bg_color, inverse)

        # Logo handling
        logo = None
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            try:
                logo = Image.open(logo_file.stream)
                logo_size = int(size * 0.2)  # Logo size relative to QR code
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            except Exception as e:
                raise ValueError(f"Invalid logo image: {str(e)}")

        # QR Code generation
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create styled image
        module_drawer = THEME_DRAWERS.get(theme, RoundedModuleDrawer())

# For gradient: use black fg initially, then modify pixels manually
        qr_fill = (0, 0, 0) if color_type == 'gradient' else fg_color
        img = qr.make_image(
    image_factory=StyledPilImage,
    fill_color=qr_fill,
    back_color=bg_color,
    module_drawer=module_drawer
).convert('RGB')

# Apply gradient AFTER qr is created
        if color_type == 'gradient':
           img = apply_gradient(img, fg_color, bg_color)

        # Resize to requested dimensions
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        # Add logo if provided
        if logo:
            img = add_logo(img, logo)

        # Apply border styling
        img = apply_border(img, border, fg_color if not inverse else bg_color, size)

        # Add title if provided
        if title:
            img = add_title(img, title, fg_color if not inverse else bg_color, size)

        # Prepare response
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return jsonify({'status': 'success', 'image': img_base64})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def add_logo(img, logo):
    """Add logo to the center of the QR code with proper transparency handling"""
    # Create a transparent background for the logo if needed
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    
    # Calculate position
    position = (
        (img.width - logo.width) // 2,
        (img.height - logo.height) // 2
    )
    
    # Create a copy to avoid modifying original
    img_copy = img.copy()
    img_copy.paste(logo, position, logo)
    return img_copy
def get_effective_colors(fg, bg, inverse):
    return (bg, fg) if inverse else (fg, bg)
def apply_gradient(img, fg_color, bg_color):
    """Apply horizontal gradient to QR code modules."""
    width, height = img.size
    fg_rgb = hex_to_rgb(fg_color)
    bg_rgb = hex_to_rgb(bg_color)
    pixels = img.load()

    for x in range(width):
        ratio = x / width
        grad_color = tuple(
            int(fg_rgb[i] * ratio + bg_rgb[i] * (1 - ratio)) for i in range(3)
        )
        for y in range(height):
            # Only modify dark modules (foreground)
            if pixels[x, y] == (0, 0, 0):
                pixels[x, y] = grad_color
    return img

def apply_border(img, border_type, color, size):
    """Apply border style to the QR code."""
    if border_type == 'none':
        return img

    border_color = hex_to_rgb(color)
    border_size = int(size * 0.05)  # 5% of image size
    
    # Common border creation
    bordered = Image.new('RGB', 
        (img.width + border_size*2, img.height + border_size*2),
        border_color)
    bordered.paste(img, (border_size, border_size))

    if border_type == 'thin':
        return bordered
    elif border_type == 'thick':
        border_size *= 2
        thick_bordered = Image.new('RGB',
            (img.width + border_size*2, img.height + border_size*2),
            border_color)
        thick_bordered.paste(img, (border_size, border_size))
        return thick_bordered
    elif border_type == 'rounded':
        mask = Image.new('L', bordered.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, *bordered.size], 
                             radius=border_size*2, fill=255)
        result = Image.new('RGB', bordered.size)
        result.paste(bordered, mask=mask)
        return result
    elif border_type == 'dotted':
        draw = ImageDraw.Draw(bordered)
        dot_size = border_size // 2
        spacing = border_size * 2
        
        # Draw dots along all four sides
        for x in range(0, bordered.width, spacing):
            draw.ellipse([x, 0, x+dot_size, dot_size], fill=border_color)
            draw.ellipse([x, bordered.height-dot_size, x+dot_size, bordered.height], 
                        fill=border_color)
        for y in range(0, bordered.height, spacing):
            draw.ellipse([0, y, dot_size, y+dot_size], fill=border_color)
            draw.ellipse([bordered.width-dot_size, y, bordered.width, y+dot_size],
                        fill=border_color)
    elif border_type == 'corners':
        draw = ImageDraw.Draw(bordered)
        corner_length = border_size * 2
        half_thickness = max(1, border_size // 2)
        
        # Draw corner brackets
        # Top-left
        draw.line([(0, border_size), (corner_length, border_size)], 
                 fill=border_color, width=half_thickness)
        draw.line([(border_size, 0), (border_size, corner_length)], 
                 fill=border_color, width=half_thickness)
        # Top-right
        draw.line([(bordered.width-corner_length, border_size), (bordered.width, border_size)],
                 fill=border_color, width=half_thickness)
        draw.line([(bordered.width-border_size, 0), (bordered.width-border_size, corner_length)],
                 fill=border_color, width=half_thickness)
        # Bottom-left
        draw.line([(0, bordered.height-border_size), (corner_length, bordered.height-border_size)],
                 fill=border_color, width=half_thickness)
        draw.line([(border_size, bordered.height-corner_length), (border_size, bordered.height)],
                 fill=border_color, width=half_thickness)
        # Bottom-right
        draw.line([(bordered.width-corner_length, bordered.height-border_size), (bordered.width, bordered.height-border_size)],
                 fill=border_color, width=half_thickness)
        draw.line([(bordered.width-border_size, bordered.height-corner_length), (bordered.width-border_size, bordered.height)],
                 fill=border_color, width=half_thickness)

    return bordered

def add_title(img, title, color, size):
    """Add title text below the QR code with proper font handling."""
    title_color = hex_to_rgb(color)
    font_size = max(10, int(size * 0.06))  # Minimum 10px font
    padding = int(size * 0.05)
    
    try:
        # Try to load Arial, fallback to default
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        # Scale default font to approximate requested size
        font.size = font_size

    # Calculate text size
    draw = ImageDraw.Draw(img)
    text_width = draw.textlength(title, font=font)
    
    # Create new image with space for title
    new_height = img.height + font_size + 2 * padding
    new_img = Image.new('RGB', (img.width, new_height), (255, 255, 255))
    new_img.paste(img, (0, 0))
    
    # Draw title
    draw = ImageDraw.Draw(new_img)
    draw.text(((img.width - text_width) // 2, img.height + padding),
             title, fill=title_color, font=font)
    
    return new_img

def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple with validation."""
    hex_color = hex_color.strip('#')
    if len(hex_color) == 3:  # Handle shorthand like #fff
        hex_color = ''.join([c*2 for c in hex_color])
    elif len(hex_color) != 6:  # Invalid format
        return (0, 0, 0)  # Default to black
    
    try:
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    except ValueError:
        return (0, 0, 0)  # Default to black on conversion error

if __name__ == '__main__':
    app.run(debug=True)