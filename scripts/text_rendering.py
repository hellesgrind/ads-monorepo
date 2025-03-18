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


def get_html_layout(request: TextRenderRequest) -> str:
    response = client.chat.completions.create(
        model="anthropic/claude-3.5-sonnet",
        messages=[
            {
                "role": "user",
                "content": f"""Given an image with dimensions {request.width}x{request.height} and the following text blocks:
                {request.text_blocks}
                Create an HTML layout that:
                1. Matches the exact dimensions
                2. Places text in the same positions
                3. Identify and specify the closest matching font
                4. Use absolute positioning
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
