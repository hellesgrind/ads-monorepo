from PIL import Image
import imgkit
import os
import tempfile


def render_html_to_image(html_content: str, width: int, height: int) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        f.write(html_content.encode("utf-8"))
        html_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        output_path = f.name

    options = {"format": "png", "width": width, "height": height, "quality": 100}

    imgkit.from_file(html_path, output_path, options=options)

    os.unlink(html_path)
    image = Image.open(output_path)
    os.unlink(output_path)

    return image
