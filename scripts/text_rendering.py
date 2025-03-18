from numpy import hanning
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

# PROMPT_INITIAL_LAYOUT = """
# You are an expert at building layouts using Tailwind and HTML.
# Layout is a background image with text blocks placed on top of it.
# For background image use placeholder image from 'changed_image.png'.
# You take screenshots of a reference web page from the user, and then build single page layouts using Tailwind and HTML.
# Also you will be given a width and height of the layout, and a list of text blocks that you need to place in the layout.
# Text blocks have a text and a bounding box.
# Bounding box is a list of 4 integers [x1, y1, x2, y2] which represent the top left and bottom right coordinates of the text block.
# - Pay close attention to text color, font size, font family, 
# padding, margin, border, etc. Match the colors, sizes and positions exactly.
# - Make sure that each text block is separated and not overlapping with other text blocks. Add padding between text blocks. Use Grid and Flexbox.


# In terms of libraries,

# - Use this script to include Tailwind: <script src="https://cdn.tailwindcss.com"></script>
# - You can use Google Fonts

# Return only the full code in <html></html> tags.
# Do not include markdown "```" or "```html" at the start or end.
# """


PROMPT_INITIAL_LAYOUT = """
You are an expert web developer specializing in creating layouts using Tailwind CSS and HTML. Your task is to generate a single-page layout based on user-provided specifications. The layout will consist of a background image with text blocks placed on top of it.
Layout is a background image with text blocks placed on top of it.
For background image use placeholder image from 'changed_image.png'.
User input will include:
1. The width and height of the layout
2. A list of text blocks, each containing:
   - The text content
   - A bounding box defined by four integers [x1, y1, x2, y2] representing the top-left and bottom-right coordinates of the text block

Your task is to create an HTML document with Tailwind CSS classes that accurately represents the provided layout. Follow these steps:

1. Analyze the input and plan the layout structure.
2. Create the HTML structure with appropriate Tailwind classes.
3. Style each text block according to its position and content.
4. Ensure that text blocks do not overlap and add padding between them.
5. Match colors, font sizes, font families, padding, margins, and borders as closely as possible to the implied design.
6. Use Grid and Flexbox for positioning when appropriate.

Important requirements:
- Pay close attention to text color, font size, font family, padding, margin, and border.
- Ensure that each text block is separated and not overlapping with other text blocks. This is crucial for the layout's integrity.
- Add appropriate padding between text blocks to maintain separation.
- Use the provided background image as a placeholder.
- Include the Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
- You may use Google Fonts if needed for better design matching.

Before generating the final HTML, wrap your layout planning process inside <layout_planning> tags in your thinking block. In this process:
1. Analyze the user input and extract key information such as layout dimensions and text block details.
2. Plan the overall layout structure, considering the placement of text blocks.
3. Consider potential design challenges (e.g., text overflow, responsive design) and propose solutions.
4. Outline the Tailwind classes you plan to use for positioning and styling.

Your final output should be the complete HTML document, including <!DOCTYPE html> and <html> tags. Do not include any markdown formatting or code block indicators. The output should consist only of the final HTML and should not duplicate or rehash any of the work you did in the layout planning section.
"""

def get_html_layout(request: TextRenderRequest) -> str:
    image_info = f"Size of layout is: width: {request.width}, height: {request.height}"
    text_blocks_info = ""
    for text_block in request.text_blocks:
        text_blocks_info += (
            f"Text block: {text_block.text}, bounding box: {text_block.bounding_box}\n"
        )
    text_blocks_info = f"Text blocks are: {text_blocks_info}"
    response = client.chat.completions.create(
        model="anthropic/claude-3.7-sonnet",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_INITIAL_LAYOUT},
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
