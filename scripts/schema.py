from pydantic import BaseModel
from typing import Literal


class TextBlockWithFontSize(BaseModel):
    text: str
    bounding_box: list[int]
    font_size: int


class TextBlockWithFontSizeAndLineSpacing(TextBlockWithFontSize):
    line_spacing: float


class TextBlockWithAlignment(TextBlockWithFontSizeAndLineSpacing):
    alignment: Literal["left", "right", "center"]


class ImageText(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlockWithFontSize]


class TextBlockWithFontName(TextBlockWithAlignment):
    font_name: str


class TextBlockWithFontNameAndColor(TextBlockWithFontName):
    color: str


class AnalyzedImage(BaseModel):
    width: int
    height: int
    text_blocks: list[TextBlockWithFontNameAndColor]
