from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io

from image_analyze import TextBlock

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


class TextRenderRequest(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlock]
    image_base64: str


PROMPT = """
You are an expert at building layouts using Tailwind and HTML.
Layout is a background image with text blocks placed on top of it.
For background image use placeholder image from 'changed_image.png'.
You take screenshots of a reference web page from the user, and then build single page layouts using Tailwind and HTML.
Also you will be given a width and height of the layout, and a list of text blocks that you need to place in the layout.
Text blocks have a text and a bounding box.
Bounding box is a list of 4 integers [x1, y1, x2, y2] which represent the top left and bottom right coordinates of the text block.
- Pay close attention to text color, font size, font family, 
padding, margin, border, etc. Match the colors, sizes and positions exactly.
- Make sure that each text block is separated and not overlapping with other text blocks. Add padding between text blocks. Use Grid and Flexbox.
- Position all text blocks from top.


In terms of libraries,

- Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
- You can use Google Fonts

Return only the full code in <html></html> tags.
Do not include markdown "```" or "```html" at the start or end.
"""

# PROMPT_2 = """
# Given an image with dimensions {request.width}x{request.height} and raw OCR text blocks:
# {request.text_blocks}

# Reference image (base64):
# {request.image_base64}

# Create a clean HTML layout that matches the original image by:
# 1. Analyzing text block intersections and merging overlapping blocks into logical content groups
# 2. Maintaining exact positioning and visual hierarchy from the original image
# 3. Ensuring font consistency within merged text blocks and sections
# 4. Identifying and specifying the closest matching font for each text group
# 5. Using absolute positioning to ensure precise placement
# 6. Preserving original text flow and relationships between elements

# The goal is to transform raw OCR blocks into a clean, structured layout that perfectly matches the source image.
# Pay special attention to maintaining consistent typography within related text sections.

# VERY IMPORTANT:
# In your response don't include ANYTHING except the HTML layout.
# Don't use ```html or ``` or any other symbols. Only the HTML layout.
# """


def get_html_layout(request: TextRenderRequest) -> str:
    image_info = f"Size of layout is: width: {request.width}, height: {request.height}"
    text_blocks_info = ""
    for text_block in request.text_blocks:
        text_blocks_info += f"Text block: {text_block.text}, bounding box: {text_block.bounding_box}\n"
    text_blocks_info = f"Text blocks are: {text_blocks_info}"
    response = client.chat.completions.create(
        model="anthropic/claude-3.7-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "text", "text": image_info},
                    {"type": "text", "text": text_blocks_info},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{request.image_base64}"
                        },
                    },
                ],
            },
        ],
    )
    return response.choices[0].message.content


def encode_image(image_path: str) -> str:
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        image_format = img.format if img.format else "JPEG"
        img.save(buffer, format=image_format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_layout_from_image(
    image_path: str,
    width: int,
    height: int,
    text_blocks: list,
) -> str:
    image_base64 = encode_image(image_path)
    request = TextRenderRequest(
        width=width,
        height=height,
        text_blocks=text_blocks,
        image_base64=image_base64,
    )
    return get_html_layout(request)
