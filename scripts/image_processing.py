import os
import time
from dotenv import load_dotenv
import fal_client
import requests
from PIL import Image, ImageDraw

from loguru import logger

from schema import TextBlockWithFontSize
from text_recognition import detect_text

load_dotenv()
os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY")


def create_image_mask(
    image_path: str,
    text_blocks: list[TextBlockWithFontSize],
    output_path: str,
) -> str:
    image = Image.open(image_path)
    text_blocks = detect_text(image)
    width, height = image.size
    mask = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(mask)

    for block in text_blocks:
        x1, y1, x3, y3 = block.bounding_box
        draw.rectangle([(x1, y1), (x3, y3)], fill="white")

    mask.save(output_path)
    return output_path


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            logger.info(log["message"])
    elif isinstance(update, fal_client.Queued):
        logger.info(f"Queued at position {update.position}")
    elif isinstance(update, fal_client.Completed):
        logger.info(update)


def remove_text_from_image(
    image_path: str,
    mask_path: str,
    output_path: str,
) -> str:
    logger.info(f"Removing text from image: {image_path}")
    image_url = fal_client.upload_file(image_path)
    logger.info(f"Uploaded image to: {image_url}")
    mask_url = fal_client.upload_file(mask_path)
    logger.info(f"Uploaded mask to: {mask_url}")

    logger.info("Calling Eraser")
    result = fal_client.subscribe(
        "fal-ai/bria/eraser",
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    logger.info(result)
    logger.info("Downloading image")
    image_url = result["image"]["url"]
    image_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(image_data)
    logger.info(f"Saved image to: {output_path}")
    return output_path


def debug_draw_bounding_boxes(
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
