from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import tempfile
import uvicorn
from main import process_image

app = FastAPI()

# Настройка CORS для разрешения всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)


class HtmlRequest(BaseModel):
    html: str


@app.post("/generate-html")
async def generate_html(image: UploadFile = File(...)):
    if not image:
        raise HTTPException(status_code=400, detail="No image provided")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_img:
        image_path = temp_img.name
        content = await image.read()
        with open(image_path, "wb") as f:
            f.write(content)

    try:
        output_path = os.path.join(tempfile.gettempdir(), "result.png")
        html_path = os.path.join(tempfile.gettempdir(), "layout.html")
        boxes_path = os.path.join(tempfile.gettempdir(), "boxes.jpeg")

        html_content = process_image(image_path, output_path, html_path, boxes_path)

        os.unlink(image_path)
        return {"html": html_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-html")
async def save_html_route(request: HtmlRequest):
    try:
        with open("saved_layout.html", "w") as f:
            f.write(request.html)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
