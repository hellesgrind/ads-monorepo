from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


class TextRenderRequest(BaseModel):
    width: int
    height: int
    text_blocks: list[dict]
    image_base64: str


class CleanedUpTextBlock(BaseModel):
    text: str
    bounding_box: list[int]


def get_html_layout(request: TextRenderRequest) -> str:
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[
            {
                "role": "user",
                "content": f"""Given an image with dimensions {request.width}x{request.height} and raw OCR text blocks:
                {request.text_blocks}

                Reference image (base64):
                {request.image_base64}

                Create a clean HTML layout that matches the original image by:
                1. Analyzing text block intersections and merging overlapping blocks into logical content groups
                2. Maintaining exact positioning and visual hierarchy from the original image
                3. Ensuring font consistency within merged text blocks and sections
                4. Identifying and specifying the closest matching font for each text group
                5. Using absolute positioning to ensure precise placement
                6. Preserving original text flow and relationships between elements

                The goal is to transform raw OCR blocks into a clean, structured layout that perfectly matches the source image.
                Pay special attention to maintaining consistent typography within related text sections.

                VERY IMPORTANT:
                In your response don't include ANYTHING except the HTML layout.
                Don't use ```html or ``` or any other symbols. Only the HTML layout.""",
            }
        ],
    )
    return response.choices[0].message.content


def encode_image(image_path: str) -> str:
    with Image.open(image_path) as img:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_layout_from_image(
    image_path: str, width: int, height: int, text_blocks: list
) -> str:
    image_base64 = encode_image(image_path)
    request = TextRenderRequest(
        width=width, height=height, text_blocks=text_blocks, image_base64=image_base64
    )
    return get_html_layout(request)
