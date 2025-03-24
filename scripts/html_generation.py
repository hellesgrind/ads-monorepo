import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

from text_recognition import TextBlockWithFontSize


def generate_html(width: int, height: int, text_blocks: list[TextBlockWithFontSize]):
    prompt = f"""
    You need to generate a HTML code for a white page with black text.
    The size of page is {width} x {height}.
    You will be given a list of text blocks.
    Every text block has a text, a bounding box and a font size.
    The text blocks are:
    {text_blocks}
    Return only the HTML code, no other text.
    Don't write ```html at the beginning and ``` at the end.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.content[0].text


if __name__ == "__main__":
    from PIL import Image
    import json
    image_path = "inputs/creo_01.png"
    width, height = Image.open(image_path).size

    with open("outputs/corrected_text.json", "r") as f:
        text_blocks = json.load(f)
    print(text_blocks)
    print(width, height)

    html = generate_html(width, height, text_blocks)
    with open("outputs/html.html", "w") as f:
        f.write(html)
