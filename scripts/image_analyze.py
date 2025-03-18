import base64
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image
import os
import json
import io
import pytesseract
import easyocr

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


class TextBlock(BaseModel):
    text: str
    bounding_box: list[int]


class ImageAnalysis(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlock]


def encode_image(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def detect_text(image: Image.Image) -> list[TextBlock]:
    reader = easyocr.Reader(["en"])
    results = reader.readtext(image)
    text_blocks = []
    for bbox, text, confidence in results:
        if confidence > 0.5:
            (x, y), (w, h) = bbox[0], bbox[2]
            x, y, w, h = int(x), int(y), int(w), int(h)
            text_blocks.append(TextBlock(text=text, bounding_box=[x, y, w - x, h - y]))
    return text_blocks


def analyze_image(image_path: str) -> ImageAnalysis:
    image = Image.open(image_path)
    width, height = image.size
    text_blocks = detect_text(image)
    return ImageAnalysis(width=width, height=height, text_blocks=text_blocks)


def draw_boxes(image_path: str, text_blocks: list[TextBlock], output_path: str = None):
    from PIL import Image, ImageDraw

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for block in text_blocks:
        x, y, w, h = block.bounding_box
        draw.rectangle([x, y, x + w, y + h], outline="white", width=2)
        draw.text((x, y - 15), block.text, fill="white")
    if output_path is None:
        output_path = "output_with_boxes.jpeg"
    image.save(output_path)
    return output_path


def merge_horizontal_boxes(
    text_blocks: list[TextBlock], threshold: int = 10
) -> list[TextBlock]:
    merged_blocks = []
    text_blocks.sort(
        key=lambda block: (block.bounding_box[1], block.bounding_box[0])
    )  # Sort by y, then x

    current_block = None
    for block in text_blocks:
        if current_block is None:
            current_block = block
        else:
            _, y1, w1, h1 = current_block.bounding_box
            x2, y2, w2, h2 = block.bounding_box

            if abs(y1 - y2) <= threshold:  # Check if on the same line
                new_x = min(current_block.bounding_box[0], x2)
                new_w = max(current_block.bounding_box[0] + w1, x2 + w2) - new_x
                new_text = current_block.text + " " + block.text
                current_block = TextBlock(
                    text=new_text,
                    bounding_box=[new_x, y1, new_w, h1],
                )
            else:
                merged_blocks.append(current_block)
                current_block = block

    if current_block is not None:
        merged_blocks.append(current_block)

    return merged_blocks


def merge_vertical_boxes(
    text_blocks: list[TextBlock], threshold: int = 10
) -> list[TextBlock]:
    if not text_blocks:
        return []

    text_blocks.sort(key=lambda block: block.bounding_box[1])

    merged_blocks = []
    current_block = text_blocks[0]

    for block in text_blocks[1:]:
        y1 = current_block.bounding_box[1] + current_block.bounding_box[3]
        next_y0 = block.bounding_box[1]

        if y1 + threshold >= next_y0:
            new_y = current_block.bounding_box[1]
            new_h = block.bounding_box[1] + block.bounding_box[3] - new_y
            new_x = min(current_block.bounding_box[0], block.bounding_box[0])
            new_w = (
                max(
                    current_block.bounding_box[0] + current_block.bounding_box[2],
                    block.bounding_box[0] + block.bounding_box[2],
                )
                - new_x
            )
            new_text = current_block.text + "\n" + block.text
            current_block = TextBlock(
                text=new_text, bounding_box=[new_x, new_y, new_w, new_h]
            )
        else:
            merged_blocks.append(current_block)
            current_block = block

    merged_blocks.append(current_block)
    return merged_blocks


if __name__ == "__main__":
    image_path = "example.jpeg"
    analysis = analyze_image(image_path)
    merged_text_blocks = merge_horizontal_boxes(analysis.text_blocks)
    analysis.text_blocks = merged_text_blocks
    output_path = draw_boxes(image_path, analysis)
    print(f"Image with boxes saved to: {output_path}")
