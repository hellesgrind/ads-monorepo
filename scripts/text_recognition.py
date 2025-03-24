import easyocr
import numpy as np
from PIL import Image
from pydantic import BaseModel


class TextBlock(BaseModel):
    text: str
    bounding_box: list[int]


class TextBlockWithFontSize(TextBlock):
    font_size: int


class ImageText(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlock]


def recognize_text(image_path: str) -> ImageText:
    image = Image.open(image_path)
    width, height = image.size
    text_blocks = _detect_text(image)
    return ImageText(width=width, height=height, text_blocks=text_blocks)


def _detect_text(image: Image) -> list[TextBlock]:
    text_blocks = []
    reader = easyocr.Reader(["en"])
    results = reader.readtext(np.array(image))

    for bbox, text, prob in results:
        if len(text) > 3:
            x1, y1 = bbox[0]
            x3, y3 = bbox[2]
            text_block = TextBlock(
                text=text,
                bounding_box=[int(x1), int(y1), int(x3), int(y3)],
            )
            text_blocks.append(text_block)

    return text_blocks


def _calculate_font_size(height: int):
    return 0


if __name__ == "__main__":
    image_path = "inputs/creo_01.png"
    result = recognize_text(image_path)

    for block in result.text_blocks:
        print(f"Found text: {block.text}")
        print(f"Position: {block.bounding_box}")
