import base64
import json
import os
import easyocr
import numpy as np
from PIL import Image, ImageDraw
import anthropic
from openai import OpenAI
from dotenv import load_dotenv
from loguru import logger

from schema import (
    TextBlockWithFontSize,
    TextBlockWithFontSizeAndLineSpacing,
    TextBlockWithAlignment,
    ImageText,
    TextBlockWithFontName,
    AnalyzedImage,
    TextBlockWithFontNameAndColor,
)

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


def analyze_image(image_path: str) -> AnalyzedImage:
    result = recognize_text(image_path)

    merged_blocks = merge_text_blocks(result.text_blocks)

    blocks_with_line_spacing = calculate_line_spacing(merged_blocks)

    corrected_blocks = correct_text_with_llm(image_path, blocks_with_line_spacing)
    blocks_with_alignment = identify_text_alignment(image_path, corrected_blocks)
    blocks_with_font_name = identify_text_font_name(image_path, blocks_with_alignment)
    blocks_with_color = identify_text_color(image_path, blocks_with_font_name)

    width, height = Image.open(image_path).size
    analyzed_image = AnalyzedImage(
        width=width,
        height=height,
        text_blocks=blocks_with_color,
    )
    return analyzed_image


def recognize_text(image_path: str) -> ImageText:
    image = Image.open(image_path)
    width, height = image.size
    text_blocks = detect_text(image)
    return ImageText(width=width, height=height, text_blocks=text_blocks)


def detect_text(image: Image) -> list[TextBlockWithFontSize]:
    text_blocks = []
    reader = easyocr.Reader(["en"])
    results = reader.readtext(np.array(image))

    for bbox, text, prob in results:
        if len(text) > 3:
            x1, y1 = bbox[0]
            x3, y3 = bbox[2]
            height = int(y3) - int(y1)
            font_size = _calculate_font_size(height)
            text_block = TextBlockWithFontSize(
                text=text,
                bounding_box=[int(x1), int(y1), int(x3), int(y3)],
                font_size=font_size,
            )
            text_blocks.append(text_block)

    return text_blocks


def _calculate_font_size(height: int) -> int:
    return int(height * 0.8)


def merge_horizontally(
    text_blocks: list[TextBlockWithFontSize], threshold: int = 10
) -> list[TextBlockWithFontSize]:
    if not text_blocks:
        return []

    blocks = text_blocks.copy()
    merged = True

    while merged:
        merged = False
        i = 0
        while i < len(blocks):
            j = i + 1
            while j < len(blocks):
                block1 = blocks[i]
                block2 = blocks[j]

                x1_1, y1_1, x3_1, y3_1 = block1.bounding_box
                x1_2, y1_2, x3_2, y3_2 = block2.bounding_box

                x_overlap = x1_1 <= x3_2 and x1_2 <= x3_1
                y_close_or_overlap = (
                    y1_1 <= y3_2 + threshold and y1_2 <= y3_1 + threshold
                )

                if x_overlap and y_close_or_overlap:
                    merged_x1 = min(x1_1, x1_2)
                    merged_y1 = min(y1_1, y1_2)
                    merged_x3 = max(x3_1, x3_2)
                    merged_y3 = max(y3_1, y3_2)
                    merged_font_size = min(block1.font_size, block2.font_size)

                    if x1_1 > x1_2:
                        merged_text = f"{block2.text} {block1.text}"
                    else:
                        merged_text = f"{block1.text} {block2.text}"

                    merged_block = TextBlockWithFontSize(
                        text=merged_text,
                        bounding_box=[merged_x1, merged_y1, merged_x3, merged_y3],
                        font_size=merged_font_size,
                    )

                    blocks[i] = merged_block
                    blocks.pop(j)

                    merged = True
                else:
                    j += 1

            i += 1

    return blocks


def merge_vertically(
    text_blocks: list[TextBlockWithFontSize], threshold: int = 10
) -> list[TextBlockWithFontSize]:
    if not text_blocks:
        return []

    blocks = text_blocks.copy()
    merged = True

    while merged:
        merged = False
        i = 0
        while i < len(blocks):
            j = i + 1
            while j < len(blocks):
                block1 = blocks[i]
                block2 = blocks[j]

                x1_1, y1_1, x3_1, y3_1 = block1.bounding_box
                x1_2, y1_2, x3_2, y3_2 = block2.bounding_box

                x_close_or_overlap = (
                    x1_1 <= x3_2 + threshold or x1_2 <= x3_1 + threshold
                )
                y_close_or_overlap = (
                    y1_1 <= y3_2 + threshold and y1_2 <= y3_1 + threshold
                )

                if x_close_or_overlap and y_close_or_overlap:
                    merged_x1 = min(x1_1, x1_2)
                    merged_y1 = min(y1_1, y1_2)
                    merged_x3 = max(x3_1, x3_2)
                    merged_y3 = max(y3_1, y3_2)
                    merged_font_size = min(block1.font_size, block2.font_size)

                    if y1_1 > y1_2:
                        merged_text = f"{block2.text}\\n{block1.text}"
                    else:
                        merged_text = f"{block1.text}\\n{block2.text}"

                    merged_block = TextBlockWithFontSize(
                        text=merged_text,
                        bounding_box=[merged_x1, merged_y1, merged_x3, merged_y3],
                        font_size=merged_font_size,
                    )

                    blocks[i] = merged_block
                    blocks.pop(j)

                    merged = True
                else:
                    j += 1

            i += 1

    return blocks


def merge_text_blocks(
    text_blocks: list[TextBlockWithFontSize], threshold: int = 10
) -> list[TextBlockWithFontSize]:
    # horizontal_merged = merge_horizontally(text_blocks, threshold)
    vertical_merged = merge_vertically(text_blocks, threshold)
    # vertical_merged = merge_vertically(horizontal_merged, threshold)
    return vertical_merged


def draw_bounding_boxes(
    image_path: str,
    text_blocks: list[TextBlockWithFontSize],
    output_path: str,
    color=(255, 0, 0),
    thickness=2,
):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    for block in text_blocks:
        x1, y1, x3, y3 = block.bounding_box
        draw.rectangle([(x1, y1), (x3, y3)], outline=color, width=thickness)

    img.save(output_path)
    return output_path


def _encode_image(image_path: str) -> tuple[str, str]:
    with open(image_path, "rb") as image_file:
        file_content = image_file.read()
        encoded_content = base64.b64encode(file_content).decode("utf-8")

        if image_path.lower().endswith(".png"):
            media_type = "image/png"
        elif image_path.lower().endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        else:
            media_type = "image/png"

        return encoded_content, media_type


def correct_text_with_llm(
    image_path: str,
    text_blocks: list[TextBlockWithFontSizeAndLineSpacing],
) -> list[TextBlockWithFontSizeAndLineSpacing]:
    prompt = """
    You will be given an image and list of detected texts.
    You need to correct the spelling and include "\n" for new lines.
    Only return the corrected text, no other text.
    Return the corrected text in JSON format in the same order as the detected texts.
    [
        {
            "text": "corrected text",
        },
        ...
    ]
    """

    text_data = [{"text": block.text} for block in text_blocks]
    text_blocks_str = json.dumps(text_data)
    prompt += f"Detected texts: {text_blocks_str}\n"

    image_data, media_type = _encode_image(image_path)

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                ],
            },
        ],
    )
    logger.info(f"text correction response: {response.content[0].text}")
    response_json = json.loads(response.content[0].text)
    logger.info(f"text correction response json: {response_json}")
    corrected_blocks = []

    for i, corrected_item in enumerate(response_json):
        if i < len(text_blocks):
            original_block = text_blocks[i].model_copy()
            original_block_dump = original_block.model_dump()
            original_block_dump.pop("text")
            corrected_blocks.append(
                TextBlockWithFontSizeAndLineSpacing(
                    text=corrected_item["text"],
                    **original_block_dump,
                )
            )

    return corrected_blocks


def _encode_image_for_openai(image_path: str) -> str:
    if image_path.endswith(".png"):
        media_type = "image/png"
    elif image_path.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    else:
        media_type = "image/png"

    with open(image_path, "rb") as image_file:
        file_content = image_file.read()
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        return f"data:{media_type};base64,{encoded_content}"


def identify_text_alignment(
    image_path: str,
    text_blocks: list[TextBlockWithFontSizeAndLineSpacing],
) -> list[TextBlockWithAlignment]:
    prompt = """
    You will be given an image and list of detected texts with their IDs.
    Your task is to determine the text alignment of each text block: left or center.
    left: if text is aligned by left border
    center: if text is aligned by center
    Only return the alignment information in this JSON format:
    [
        {
            "id": 0,
            "alignment": "left" or "center"
        },
        ...
    ]
    Do not write any other text, don't write ```json or ```
    """

    text_data = [{"id": i, "text": block.text} for i, block in enumerate(text_blocks)]
    text_blocks_str = json.dumps(text_data)
    prompt += f"Detected texts: {text_blocks_str}\n"

    image_data = _encode_image_for_openai(image_path)

    response = openai_client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data,
                        },
                    },
                ],
            },
        ],
    )
    logger.info(f"text alignment response: {response.choices[0].message.content}")
    response_json = json.loads(response.choices[0].message.content)
    logger.info(f"text alignment response json: {response_json}")

    result_blocks = []
    for item in response_json:
        text_id = int(item["id"])
        original_text_block = text_blocks[text_id]
        result_blocks.append(
            TextBlockWithAlignment(
                alignment=item["alignment"],
                **original_text_block.model_dump(),
            )
        )
    return result_blocks


def identify_text_font_name(
    image_path: str,
    text_blocks: list[TextBlockWithFontSizeAndLineSpacing],
) -> list[TextBlockWithFontName]:
    prompt = """
    You will be given an image and list of detected texts with their IDs.
    Your task is to determine the text font name of each text block.
    Find the closest match from the Google Fonts library.
    Only return the font name information in this JSON format:
    [
        {
            "id": 0,
            "font_name": 
        },
        ...
    ]
    Do not write any other text, don't write ```json or ```
    """

    text_data = [{"id": i, "text": block.text} for i, block in enumerate(text_blocks)]
    text_blocks_str = json.dumps(text_data)
    prompt += f"Detected texts: {text_blocks_str}\n"

    image_data = _encode_image_for_openai(image_path)

    response = openai_client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data,
                        },
                    },
                ],
            },
        ],
    )
    logger.info(f"text alignment response: {response.choices[0].message.content}")
    response_json = json.loads(response.choices[0].message.content)
    logger.info(f"text alignment response json: {response_json}")

    result_blocks = []
    for item in response_json:
        text_id = int(item["id"])
        original_text_block = text_blocks[text_id]
        result_blocks.append(
            TextBlockWithFontName(
                font_name=item["font_name"],
                **original_text_block.model_dump(),
            )
        )
    return result_blocks


def identify_text_color(
    image_path: str,
    text_blocks: list[TextBlockWithFontSizeAndLineSpacing],
) -> list[TextBlockWithFontNameAndColor]:
    prompt = """
    You will be given an image and list of detected texts with their IDs.
    Your task is to determine the text color of each text block.
    Only return the color information in this JSON format:
    [
        {
            "id": 0,
            "color": "hex color code"
        },
        ...
    ]
    Do not write any other text, don't write ```json or ```
    """

    text_data = [{"id": i, "text": block.text} for i, block in enumerate(text_blocks)]
    text_blocks_str = json.dumps(text_data)
    prompt += f"Detected texts: {text_blocks_str}\n"

    image_data = _encode_image_for_openai(image_path)

    response = openai_client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data,
                        },
                    },
                ],
            },
        ],
    )
    logger.info(f"text color response: {response.choices[0].message.content}")
    response_json = json.loads(response.choices[0].message.content)
    logger.info(f"text color response json: {response_json}")

    result_blocks = []
    for item in response_json:
        text_id = int(item["id"])
        original_text_block = text_blocks[text_id]
        result_blocks.append(
            TextBlockWithFontNameAndColor(
                color=item["color"],
                **original_text_block.model_dump(),
            )
        )
    return result_blocks


def _block_line_spacing(text_block: TextBlockWithFontSize) -> int:
    text = text_block.text
    lines_count = text.count("\\n") + 1

    if lines_count <= 1:
        return 0

    _, y1, _, y3 = text_block.bounding_box
    height = y3 - y1
    avg_line_height = height / lines_count
    line_spacing = avg_line_height - text_block.font_size

    return int(line_spacing)


def calculate_line_spacing(
    text_blocks: list[TextBlockWithFontSize],
) -> list[TextBlockWithFontSize]:
    blocks_with_line_spacing = []
    for block in text_blocks:
        line_spacing = _block_line_spacing(block)
        blocks_with_line_spacing.append(
            TextBlockWithFontSizeAndLineSpacing(
                text=block.text,
                bounding_box=block.bounding_box,
                font_size=block.font_size,
                line_spacing=line_spacing,
            )
        )
    return blocks_with_line_spacing

