import os
import uuid
from pathlib import Path
from typing import List, Literal

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database

DB_PATH = os.environ.get("DB_PATH", "catalog.db")
UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}

Path(UPLOADS_DIR).mkdir(exist_ok=True)
database.init_db(DB_PATH)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
templates = Jinja2Templates(directory="templates")


def _items_with_images():
    items = database.list_items()
    return [(dict(item), [dict(img) for img in database.get_images(item["id"])]) for item in items]


@app.get("/", response_class=HTMLResponse)
def admin_list(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "items_with_images": _items_with_images(),
    })


@app.get("/catalog", response_class=HTMLResponse)
def public_catalog(request: Request):
    return templates.TemplateResponse(request, "catalog.html", {
        "items_with_images": _items_with_images(),
    })


@app.get("/items/new", response_class=HTMLResponse)
def new_item_form(request: Request):
    return templates.TemplateResponse(request, "item_form.html", {
        "item": None,
        "images": [],
    })


@app.post("/items/new")
async def create_item(
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: Literal["available", "sold"] = Form("available"),
    images: List[UploadFile] = File(default=[]),
):
    item_id = database.create_item(title=title, description=description, price=price, status=status)
    for i, image in enumerate(images):
        if image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                ext = ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            dest = Path(UPLOADS_DIR) / filename
            dest.write_bytes(await image.read())
            database.add_image(item_id, filename=filename, sort_order=i)
    return RedirectResponse("/", status_code=303)


@app.get("/items/{item_id}/edit", response_class=HTMLResponse)
def edit_item_form(item_id: int, request: Request):
    row = database.get_item(item_id)
    if row is None:
        raise HTTPException(status_code=404)
    item = dict(row)
    images = [dict(img) for img in database.get_images(item_id)]
    return templates.TemplateResponse(request, "item_form.html", {
        "item": item,
        "images": images,
    })


@app.post("/items/{item_id}/edit")
async def update_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: Literal["available", "sold"] = Form("available"),
    images: List[UploadFile] = File(default=[]),
):
    if database.get_item(item_id) is None:
        raise HTTPException(status_code=404)
    database.update_item(item_id, title=title, description=description, price=price, status=status)
    existing_count = len(database.get_images(item_id))
    for i, image in enumerate(images):
        if image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                ext = ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            dest = Path(UPLOADS_DIR) / filename
            dest.write_bytes(await image.read())
            database.add_image(item_id, filename=filename, sort_order=existing_count + i)
    return RedirectResponse(f"/items/{item_id}/edit", status_code=303)


@app.post("/items/{item_id}/delete")
def delete_item_route(item_id: int):
    for img in database.get_images(item_id):
        (Path(UPLOADS_DIR) / img["filename"]).unlink(missing_ok=True)
    database.delete_item(item_id)
    return RedirectResponse("/", status_code=303)


@app.post("/items/{item_id}/images/{image_id}/delete")
def delete_image_route(item_id: int, image_id: int):
    for img in database.get_images(item_id):
        if img["id"] == image_id:
            (Path(UPLOADS_DIR) / img["filename"]).unlink(missing_ok=True)
            database.delete_image(image_id)
            break
    return RedirectResponse(f"/items/{item_id}/edit", status_code=303)
