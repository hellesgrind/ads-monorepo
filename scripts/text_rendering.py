from numpy import hanning
from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io

from image_analyze import TextBlock, TextBlockWithFont

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def encode_image(image_path: str) -> str:
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        image_format = img.format if img.format else "JPEG"
        img.save(buffer, format=image_format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def create_html_layout(
    image_path: str,
    text_blocks: list[TextBlockWithFont],
) -> str:
    width, height = Image.open(image_path).size
    text_blocks_info = ""
    for text_block in text_blocks:
        x, y, w, h = text_block.bounding_box
        text_blocks_info += (
            f"Text block: {text_block.text}, x: {x}, y: {y}, w: {w}, h: {h}, "
            f"font: {text_block.font}, font_size: {text_block.font_size}, "
            f"font_style: {text_block.font_style}, color: {text_block.color}\n"
        )

    prompt = f"""
    You are an expert at building layouts using Tailwind and HTML.
    Layout is a background image with text blocks placed on top of it.
    For background image use placeholder 'cleaned_image.png'.
    You need to build a layout HTML code using Tailwind and HTML with width: {width}px and height: {height}px.
    And place text blocks in the layout.
    For each text block you have the following information:
    - text: text to place in the text block
    - x: x coordinate of the text block starting from the top left corner of the image
    - y: y coordinate of the text block starting from the top left corner of the image
    - w: width of the text block
    - h: height of the text block
    - font: font of the text block
    - font_size: size of the font. Can be s, m or l.
    - font_style: style of the font. Can be bold or normal.
    - color: color of the text block

    Very important:
    For font size use the following classes:
    .custom-text-s {{
      font-size: calc({width}px * 0.0125);
    }}
    .custom-text-m {{
      font-size: calc({width}px * 0.025);
    }}  
    .custom-text-l {{
      font-size: calc({width}px * 0.05);
    }}
    
    In terms of libraries,

    - Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
    - You can use Google Fonts

    Return only the full code in <html></html> tags.
    Do not include markdown "```" or "```html" at the start or end.

    Text blocks:
    {text_blocks_info}
    """
    response = client.chat.completions.create(
        model="anthropic/claude-3.7-sonnet",
        messages=[
            {"role": "user", "content": [{"type": "text", "text": prompt}]},
        ],
    )
    response_text = response.choices[0].message.content
    if response_text.startswith("```html"):
        response_text = response_text[len("```html") :]
    if response_text.endswith("```"):
        response_text = response_text[: -len("```")]
    return response_text
