import base64
import json
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image
import os
import io
import easyocr
import numpy as np

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


class TextBlock(BaseModel):
    text: str
    bounding_box: list[int]


class TextBlockWithFont(TextBlock):
    font: str
    font_size: str
    font_style: str
    color: str


class CorrectedTextBlockWithFont(TextBlockWithFont):
    corrected_text: str


class ImageAnalysis(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlock]


def analyze_image(image_path: str) -> ImageAnalysis:
    image = Image.open(image_path)
    width, height = image.size
    text_blocks = _detect_text(image)
    return ImageAnalysis(width=width, height=height, text_blocks=text_blocks)


def identify_text_blocks_fonts(
    image_path: str,
    text_blocks: list[TextBlock],
) -> list[TextBlockWithFont]:
    image = Image.open(image_path)
    width, height = image.size
    text_block_str = "\n".join(
        [f"{block.text} - {block.bounding_box}" for block in text_blocks]
    )
    print(text_block_str)
    prompt = f"""
    You will be given an image with width: {width}px and height: {height}px.
    And recognized text blocks in the image.
    Your task is to identify the font, font size and font style of each text block.
    Return the result in the following format:
    [
        {{
            "text": "text",
            "bounding_box": [x, y, w, h],
            "font": "font name", # Font name from Google Fonts
            "font_size": str, # s, m, or l
            "font_style": str, # "bold" or "normal"
            "color": str,
        }},
        ...
    ]
    Guidelines:
    - Do not change the text or the bounding box.
    - The font is the closest match from the Google Fonts.
    - The font style is either "bold" or "normal".
    - The font size can be s, m, or l.
    - Do not include markdown "```" or "```json" at the start or end.
    Text blocks:
    {text_block_str}
    """
    image_base64 = _encode_image(image)
    response = client.chat.completions.create(
        model="openai/gpt-4.5-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            },
        ],
    )
    response_text = response.choices[0].message.content
    print(response_text)
    if response_text.startswith("```json"):
        response_text = response_text[len("```json") :]
    if response_text.endswith("```"):
        response_text = response_text[: -len("```")]
    data = json.loads(response_text)
    text_blocks = []
    for box in data:
        x, y, w, h = box["bounding_box"]
        x, y, w, h = int(x), int(y), int(w), int(h)
        color = box["color"]
        font = box["font"]
        font_size = box["font_size"]
        font_style = box["font_style"]
        text = box["text"]
        text_blocks.append(
            TextBlockWithFont(
                text=text,
                bounding_box=[x, y, w, h],
                font=font,
                font_size=font_size,
                font_style=font_style,
                color=color,
            )
        )
    return text_blocks


def correct_text_blocks_coordinates(
    image_path: str,
    text_blocks: list[TextBlockWithFont],
) -> list[CorrectedTextBlockWithFont]:
    corrected_blocks = []
    blocks_to_process = text_blocks.copy()
    threshold = 10

    while blocks_to_process:
        current_block = blocks_to_process.pop(0)
        x1, y1, w1, h1 = current_block.bounding_box

        for i, block in enumerate(blocks_to_process):
            x2, y2, w2, h2 = block.bounding_box

            x_changed = False
            y_changed = False

            if abs(x1 - x2) < threshold:
                min_x = min(x1, x2)
                blocks_to_process[i].bounding_box[0] = min_x
                x1 = min_x
                x_changed = True

            if abs(y1 - y2) < threshold:
                min_y = min(y1, y2)
                blocks_to_process[i].bounding_box[1] = min_y
                y1 = min_y
                y_changed = True

            if x_changed or y_changed:
                current_block.bounding_box[0] = x1
                current_block.bounding_box[1] = y1

        corrected_blocks.append(
            CorrectedTextBlockWithFont(
                text=current_block.text,
                bounding_box=current_block.bounding_box,
                font=current_block.font,
                font_size=current_block.font_size,
                font_style=current_block.font_style,
                color=current_block.color,
                corrected_text=current_block.text,
            )
        )

    return corrected_blocks


def clean_text_blocks(text_blocks: list[TextBlock]) -> list[TextBlock]:
    cleaned_text_blocks = []
    for block in text_blocks:
        text = block.text
        text = text.replace("\n", " ")
        text = text.strip()
        if text:
            cleaned_text_blocks.append(
                TextBlock(text=text, bounding_box=block.bounding_box)
            )
    return cleaned_text_blocks


def draw_boxes(image_path: str, text_blocks: list[TextBlock], output_path: str = None):
    from PIL import Image, ImageDraw

    image = Image.open(image_path)
    image_format = image.format
    draw = ImageDraw.Draw(image)
    for block in text_blocks:
        x, y, w, h = block.bounding_box
        draw.rectangle([x, y, x + w, y + h], outline="white", width=2)
        draw.text((x, y - 15), block.text, fill="white")
    if output_path is None:
        output_path = f"output_with_boxes.{image_format.lower()}"
    image.save(output_path, format=image_format)
    return output_path


def merge_horizontal_boxes(
    text_blocks: list[TextBlock], threshold: int = 10
) -> list[TextBlock]:
    merged_blocks = []
    text_blocks.sort(key=lambda block: (block.bounding_box[1], block.bounding_box[0]))

    current_block = None
    for block in text_blocks:
        if current_block is None:
            current_block = block
        else:
            x1, y1, w1, h1 = current_block.bounding_box
            x2, y2, w2, h2 = block.bounding_box

            if abs(y1 - y2) <= threshold:
                new_x = min(x1, x2)
                new_w = max(x1 + w1, x2 + w2) - new_x
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
        x1, y1, w1, h1 = current_block.bounding_box
        x2, y2, w2, h2 = block.bounding_box

        bottom_y1 = y1 + h1

        if bottom_y1 + threshold >= y2:
            new_y = y1
            new_h = (y2 + h2) - new_y
            new_x = min(x1, x2)
            new_w = max(x1 + w1, x2 + w2) - new_x
            new_text = current_block.text + "\n" + block.text
            current_block = TextBlock(
                text=new_text, bounding_box=[new_x, new_y, new_w, new_h]
            )
        else:
            merged_blocks.append(current_block)
            current_block = block

    merged_blocks.append(current_block)
    return merged_blocks


def _encode_image(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image_format = image.format if image.format else "JPEG"
    image.save(buffer, format=image_format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _detect_text(image: Image.Image) -> list[TextBlock]:
    reader = easyocr.Reader(["en"])
    image_np = np.array(image)
    results = reader.readtext(image_np)
    text_blocks = []
    for bbox, text, confidence in results:
        if confidence > 0.4:
            (x1, y1), (x2, y2) = bbox[0], bbox[2]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w = x2 - x1
            h = y2 - y1
            text_blocks.append(TextBlock(text=text, bounding_box=[x1, y1, w, h]))
    return text_blocks
