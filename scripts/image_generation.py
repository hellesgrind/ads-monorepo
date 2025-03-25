
from loguru import logger
import requests
from PIL import Image
import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.Queued):
        logger.info(f"Queued at position {update.position}")
    elif isinstance(update, fal_client.InProgress):
        for log in update.logs:
            logger.info(log["message"])
    elif isinstance(update, fal_client.Completed):
        logger.info(update)

def regenerate_image(image_path: str, output_path: str):
    image_url = fal_client.upload_file(image_path)
    width, height = Image.open(image_path).size
    logger.info(f"Regenerating image with size {width}x{height}")
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
    logger.info(result)
    image_url = result["images"][0]["url"]
    image_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path
