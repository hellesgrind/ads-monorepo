import base64
import json
import os
import easyocr
import numpy as np
from PIL import Image, ImageDraw
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)


# class TextBlock(BaseModel):
#     text: str
#     bounding_box: list[int]


class TextBlockWithFontSize(BaseModel):
    text: str
    bounding_box: list[int]
    font_size: int


class ImageText(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlockWithFontSize]


def recognize_text(image_path: str) -> ImageText:
    image = Image.open(image_path)
    width, height = image.size
    text_blocks = _detect_text(image)
    return ImageText(width=width, height=height, text_blocks=text_blocks)


def _detect_text(image: Image) -> list[TextBlockWithFontSize]:
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
    return int(height * 0.75)


def merge_text_blocks(
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
                    x1_1 <= x3_2 + threshold and x1_2 <= x3_1 + threshold
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
    text_blocks: list[TextBlockWithFontSize],
) -> list[TextBlockWithFontSize]:
    prompt = """
    You will be given an image and list of detected texts.
    You need to correct the spelling.
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

    response_json = json.loads(response.content[0].text)
    print(response_json)
    corrected_blocks = []

    for i, corrected_item in enumerate(response_json):
        if i < len(text_blocks):
            corrected_blocks.append(
                TextBlockWithFontSize(
                    text=corrected_item["text"],
                    bounding_box=text_blocks[i].bounding_box,
                    font_size=text_blocks[i].font_size,
                )
            )

    return corrected_blocks


if __name__ == "__main__":
    image_path = "inputs/creo_01.png"
    result = recognize_text(image_path)

    merged_blocks = merge_text_blocks(result.text_blocks)

    output_path = "outputs/recognized_text.png"
    draw_bounding_boxes(image_path, merged_blocks, output_path)
    for block in merged_blocks:
        print(f"Found text: {block.text}")
        print(f"Position: {block.bounding_box}")
        print(f"Font size: {block.font_size}")
    print(f"Image with bounding boxes saved to: {output_path}")
    corrected_blocks = correct_text_with_llm(image_path, merged_blocks)
    with open("outputs/corrected_text.json", "w") as f:
        blocks_data = [
            {
                "text": block.text,
                "bounding_box": block.bounding_box,
                "font_size": block.font_size,
            }
            for block in corrected_blocks
        ]
        json.dump(blocks_data, f, indent=4)
    # for block in corrected_blocks:
    #     print(f"Found text: {block.text}")
    #     print(f"Position: {block.bounding_box}")
