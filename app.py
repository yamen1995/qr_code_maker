from flask import Flask, render_template, request, send_file
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask, SolidFillColorMask
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
    color_type = request.form.get('colortype', 'solid')
    fg_hex = request.form.get('fg', '#000000')
    bg_hex = request.form.get('bg', '#ffffff')
    fg_color = hex_to_rgb(fg_hex)
    bg_color = hex_to_rgb(bg_hex)

    # Choose color mask
    if color_type == 'gradient':
        color_mask = RadialGradiantColorMask(center_color=fg_color, edge_color=bg_color)
    else:
        color_mask = SolidFillColorMask(front_color=fg_color, back_color=bg_color)

    # Build QR code
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=color_mask
    )

    # Save image to a BytesIO buffer as PNG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    # Return the image as a file
    return send_file(
        img_buffer,
        mimetype='image/png',
        as_attachment=False,
        download_name='qr_code.png'
    )
if __name__ == '__main__':
    app.run(debug=True)