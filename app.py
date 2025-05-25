from flask import Flask, render_template, request, send_file
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, GappedSquareModuleDrawer,
    HorizontalBarsDrawer, VerticalBarsDrawer, CircleModuleDrawer
)
from qrcode.image.styles.colormasks import (
    SolidFillColorMask, RadialGradiantColorMask
)
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import io

app = Flask(__name__)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_qr():
    data = request.form['qrdata']
    fg_color = hex_to_rgb(request.form.get('fg', '#000000'))
    bg_color = hex_to_rgb(request.form.get('bg', '#ffffff'))
    color_type = request.form.get('colortype', 'solid')
    theme = request.form.get('theme', 'rounded')
    title_text = request.form.get('title', '').strip()
    border_style = request.form.get('border', 'none')

    # New: get requested size (default 300px)
    try:
        desired_size = int(request.form.get('size', 300))
        if desired_size < 100:
            desired_size = 100  # minimum size to avoid too small
    except ValueError:
        desired_size = 300

    # Color mask
    if color_type == 'gradient':
        color_mask = RadialGradiantColorMask(center_color=fg_color, edge_color=bg_color)
    else:
        color_mask = SolidFillColorMask(front_color=fg_color, back_color=bg_color)

    # Module drawer (theme)
    drawer_map = {
        'rounded': RoundedModuleDrawer(),
        'gapped': GappedSquareModuleDrawer(),
        'horizontal': HorizontalBarsDrawer(),
        'vertical': VerticalBarsDrawer(),
        'circle': CircleModuleDrawer()
    }
    module_drawer = drawer_map.get(theme, RoundedModuleDrawer())

    # --- Calculate dynamic box_size ---
    # First create a temporary QRCode without box_size to get matrix size
    temp_qr = qrcode.QRCode(border=4)
    temp_qr.add_data(data)
    temp_qr.make(fit=True)
    matrix_size = len(temp_qr.get_matrix())  # number of modules per side
    border = 4

    # Calculate box_size so final image is close to desired_size (pixels)
    box_size = max(1, desired_size // (matrix_size + 2 * border))

    # Now create QRCode with computed box_size
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer,
        color_mask=color_mask
    ).convert("RGB")

    # Add title if provided
    if title_text:
        font_path = str(Path("C:/Windows/Fonts/arial.ttf"))  # Update if needed for Linux/Mac
        font = ImageFont.truetype(font_path, size=28)
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), title_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        new_width = max(qr_img.width, text_width + 20)
        new_height = qr_img.height + text_height + 20

        new_img = Image.new("RGB", (new_width, new_height), color=bg_color)
        draw = ImageDraw.Draw(new_img)
        draw.text(((new_width - text_width) // 2, 10), title_text, fill=fg_color, font=font)
        new_img.paste(qr_img, ((new_width - qr_img.width) // 2, text_height + 20))
        qr_img = new_img

    # Add border if requested
    if border_style != 'none':
        border_thickness = 4 if border_style == 'thin' else 16
        border_color = fg_color if border_style != 'thin' else (0, 0, 0)
        new_size = (qr_img.width + 2 * border_thickness, qr_img.height + 2 * border_thickness)

        bordered_img = Image.new("RGB", new_size, color=border_color)
        bordered_img.paste(qr_img, (border_thickness, border_thickness))

        if border_style == 'rounded':
            # Add rounded corners by masking
            mask = Image.new("L", new_size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([0, 0, *new_size], radius=20, fill=255)
            qr_img = Image.composite(bordered_img, Image.new("RGB", new_size, bg_color), mask)
        else:
            qr_img = bordered_img

    # Return image
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=False, download_name='qr_code.png')

@app.route('/preview', methods=['POST'])
def preview_qr():
    return generate_qr()
if __name__ == '__main__':
    app.run(debug=True)