from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import tempfile
import shutil
import uvicorn
import base64
from main import process_image

app = FastAPI()
CACHE_DIR = "static"

os.makedirs(CACHE_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=CACHE_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HtmlRequest(BaseModel):
    html: str


@app.post("/generate-html")
async def generate_html(image: UploadFile = File(...)):
    import uuid
    unique_id = str(uuid.uuid4())
    session_dir = os.path.join(CACHE_DIR, unique_id)
    os.makedirs(session_dir, exist_ok=True)
    temp_dir = os.path.join(session_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    input_image_path = os.path.join(temp_dir, f"input_{unique_id}.png")
    output_path = os.path.join(temp_dir, f"result_{unique_id}.png")
    html_path = os.path.join(temp_dir, f"layout_{unique_id}.html")
    boxes_path = os.path.join(temp_dir, f"boxes_{unique_id}.jpeg")

    with open(input_image_path, "wb") as f:
        content = await image.read()
        f.write(content)

    html_content = process_image(input_image_path, output_path, html_path, boxes_path)

    changed_image_path = os.path.join(session_dir, "changed_image.png")

    static_image_path = os.path.join(session_dir, f"changed_image_{unique_id}.png")
    shutil.copy(changed_image_path, static_image_path)

    image_url = os.path.join(session_dir, f"changed_image_{unique_id}.png")

    html_with_image = f"""
    {html_content}
    <div class="image-container">
        <img src="{image_url}" alt="Generated Image" style="max-width: 100%; margin-top: 20px;">
    </div>
    """

    os.unlink(input_image_path)

    return {"html": html_with_image, "imageUrl": image_url}


# @app.post("/save-html")
# async def save_html_route(request: HtmlRequest):
#     try:
#         with open("saved_layout.html", "w") as f:
#             f.write(request.html)
#         return {"success": True}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join(CACHE_DIR, image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
