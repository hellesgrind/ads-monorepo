import os
from dotenv import load_dotenv
import fal_client
import requests
from image_analyze import TextBlock
from PIL import Image, ImageDraw
import base64

load_dotenv()
os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY")


def create_image_mask(
    image_path: str,
    text_blocks: list[TextBlock],
    output_path: str,
) -> str:
    image = Image.open(image_path)
    width, height = image.size
    mask = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(mask)

    for block in text_blocks:
        x, y, w, h = block.bounding_box
        draw.rectangle([x, y, x + w, y + h], fill="white")

    mask.save(output_path)
    return output_path

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])


def remove_text_from_image(
    image_path: str,
    text_blocks: list[TextBlock],
    output_path: str,
) -> str:
    image_url = fal_client.upload_file(image_path)
    mask_path = "temp_mask.png"
    create_image_mask(image_path, text_blocks, mask_path)
    mask_url = fal_client.upload_file(mask_path)
    # os.remove(mask_path)

    result = fal_client.subscribe(
        "fal-ai/bria/eraser",
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    print(result)
    image_url = result["image"]["url"]
    image_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path


def regenerate_image(image_path: str, output_path: str):
    image_url = fal_client.upload_file(image_path)
    width, height = Image.open(image_path).size
    result = fal_client.subscribe(
        "fal-ai/flux-pro/v1.1/redux",
        arguments={
            "image_size": {
                "width": width,
                "height": height
            },
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "safety_tolerance": "2",
            "output_format": "png",
            "image_url": image_url,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    print(result)
    image_url = result["images"][0]["url"]
    image_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path
