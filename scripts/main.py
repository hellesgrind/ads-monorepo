import json
import os
import shutil
from html_generation import generate_html
from image_processing import (
    debug_draw_bounding_boxes,
    remove_text_from_image,
    create_image_mask,
)
from image_generation import regenerate_image
from text_recognition import analyze_image


CACHE_DIR = "cache"


def clone_image(image_path: str, output_dir: str):
    # shutil.copy(image_path, os.path.join(output_dir, "original.png"))
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # analyzed_image = analyze_image(image_path)
    # with open(
    #     os.path.join(output_dir, "analyzed_image.json"), "w", encoding="utf-8"
    # ) as f:
    #     json.dump(analyzed_image.model_dump(), f, indent=4)
    with open(
        os.path.join(output_dir, "analyzed_image.json"), "r", encoding="utf-8"
    ) as f:
        from schema import AnalyzedImage
        analyzed_image = AnalyzedImage(**json.load(f))

    text_mask_path = os.path.join(output_dir, "text_mask.png")
    create_image_mask(
        image_path=image_path,
        text_blocks=analyzed_image.text_blocks,
        output_path=text_mask_path,
    )
    cleaned_image_path = os.path.join(output_dir, "cleaned.png")
    # remove_text_from_image(image_path, text_mask_path, cleaned_image_path)

    regenerated_image_path = os.path.join(output_dir, "regenerated.png")
    regenerate_image(cleaned_image_path, regenerated_image_path)

    html_code = generate_html(
        height=analyzed_image.height,
        width=analyzed_image.width,
        text_blocks=analyzed_image.text_blocks,
        image_path=regenerated_image_path,
    )
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_code)


if __name__ == "__main__":
    clone_image("inputs/creo_01.png", os.path.join(CACHE_DIR, "creo_01"))
