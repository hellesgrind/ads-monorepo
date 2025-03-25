import os
from loguru import logger
import requests
from PIL import Image
import fal_client
from openai import OpenAI
from dotenv import load_dotenv
from text_recognition import _encode_image_for_openai

load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def on_queue_update(update):
    if isinstance(update, fal_client.Queued):
        logger.info(f"Queued at position {update.position}")
    elif isinstance(update, fal_client.InProgress):
        for log in update.logs:
            logger.info(log["message"])
    elif isinstance(update, fal_client.Completed):
        logger.info(update)

def regenerate_image_flux_pro_redux(
    image_path: str,
    output_path: str,
    prompt: str,
):
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


def regenerate_image_flux_dev_redux(
    image_path: str,
    output_path: str,
):
    image_url = fal_client.upload_file(image_path)
    width, height = Image.open(image_path).size
    logger.info(f"Regenerating image using Flux Dev Redux with size {width}x{height}")
    result = fal_client.subscribe(
        "fal-ai/flux/dev/redux",
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
    
def generate_prompt(image_path: str) -> str:
    prompt = """
    You need to generate a prompt for image generation.
    You will be given an image.
    Describe the image briefly. Describe all important details such as objects, people e.t.c.
    Describe the positions of main objects on image.
    But then slightly change the appearance of objects - vary colors, appearance of 
    characters, etc. Make sure image have the same idea and composition but is a
    variation of the original image.
    Return only the prompt, nothing else, don't include anything else 
    like "Here is the prompt:" or "Prompt:" or anything like that.
    """
    encoded_image = _encode_image_for_openai(image_path)
    response = openai_client.chat.completions.create(
        model="gpt-4.5-preview",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": encoded_image,
                    },
                },
            ]},
        ],
    )
    logger.info(f"Prompt generation response: {response.choices[0].message.content}")
    return response.choices[0].message.content
