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

# Создадим директорию для статических файлов, если её нет
os.makedirs("static", exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

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

    # Генерируем уникальное имя для файла
    import uuid

    unique_id = str(uuid.uuid4())

    # Пути для файлов
    temp_dir = tempfile.gettempdir()
    input_image_path = os.path.join(temp_dir, f"input_{unique_id}.png")
    output_path = os.path.join(temp_dir, f"result_{unique_id}.png")
    html_path = os.path.join(temp_dir, f"layout_{unique_id}.html")
    boxes_path = os.path.join(temp_dir, f"boxes_{unique_id}.jpeg")

    # Сохраняем загруженное изображение
    with open(input_image_path, "wb") as f:
        content = await image.read()
        f.write(content)

    try:
        # Обрабатываем изображение
        html_content = process_image(
            input_image_path, output_path, html_path, boxes_path
        )

        # Путь для сохранения измененного изображения (changed_image.png)
        changed_image_path = os.path.join(temp_dir, "changed_image.png")

        # Копируем changed_image.png в статическую директорию
        static_image_path = f"static/changed_image_{unique_id}.png"
        shutil.copy(changed_image_path, static_image_path)

        # Получаем полный URL изображения
        image_url = f"/static/changed_image_{unique_id}.png"

        # Добавляем изображение в HTML-код
        html_with_image = f"""
        {html_content}
        <div class="image-container">
          <img src="{image_url}" alt="Generated Image" style="max-width: 100%; margin-top: 20px;">
        </div>
        """

        os.unlink(input_image_path)

        return {"html": html_with_image, "imageUrl": image_url}
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


@app.get("/images/{image_name}")
async def get_image(image_name: str):
    image_path = f"static/{image_name}"
    if os.path.exists(image_path):
        return FileResponse(image_path)
    raise HTTPException(status_code=404, detail="Image not found")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
