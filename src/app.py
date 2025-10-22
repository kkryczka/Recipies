from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import json

from . import crud, models, schemas
from .db import SessionLocal, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB once at startup
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    recipes = crud.get_recipes(db)
    # decode JSON fields for template
    out = []
    for r in recipes:
        out.append({
            "id": r.id,
            "name": r.name,
            "ingredients": json.loads(r.ingredients) if r.ingredients else [],
            "steps": json.loads(r.steps) if r.steps else [],
        })
    # TemplateResponse now prefers (request, name) signature in newer Starlette
    return templates.TemplateResponse(request, "index.html", {"recipes": out})


@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def view_recipe(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    r = crud.get_recipe(db, recipe_id)
    if not r:
        raise HTTPException(status_code=404)
    recipe = {"id": r.id, "name": r.name, "ingredients": json.loads(r.ingredients or '[]'), "steps": json.loads(r.steps or '[]')}
    return templates.TemplateResponse(request, "view.html", {"recipe": recipe})


@app.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def edit_recipe_form(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    r = crud.get_recipe(db, recipe_id)
    if not r:
        raise HTTPException(status_code=404)
    recipe = {"id": r.id, "name": r.name, "ingredients": "\n".join(json.loads(r.ingredients or '[]')), "steps": "\n".join(json.loads(r.steps or '[]'))}
    return templates.TemplateResponse(request, "edit.html", {"recipe": recipe})


@app.post("/recipes/{recipe_id}/edit")
def edit_recipe(recipe_id: int, name: str = Form(...), ingredients: str = Form(""), steps: str = Form(""), db: Session = Depends(get_db)):
    ing = [i.strip() for i in ingredients.splitlines() if i.strip()]
    st = [s.strip() for s in steps.splitlines() if s.strip()]
    recipe_in = schemas.RecipeCreate(name=name, ingredients=ing, steps=st)
    updated = crud.update_recipe(db, recipe_id, recipe_in)
    if not updated:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=f'/recipes/{recipe_id}', status_code=303)


@app.post("/recipes/{recipe_id}/delete")
def delete_recipe_route(recipe_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_recipe(db, recipe_id)
    if not ok:
        raise HTTPException(status_code=404)
    return RedirectResponse(url='/', status_code=303)


@app.post("/recipes")
def create_recipe(name: str = Form(...), ingredients: str = Form(""), steps: str = Form(""), db: Session = Depends(get_db)):
    # ingredients and steps are newline-separated in form
    ing = [i.strip() for i in ingredients.splitlines() if i.strip()]
    st = [s.strip() for s in steps.splitlines() if s.strip()]
    recipe_in = schemas.RecipeCreate(name=name, ingredients=ing, steps=st)
    existing = crud.get_recipe_by_name(db, name)
    if existing:
        raise HTTPException(status_code=400, detail="Recipe with that name already exists")
    r = crud.create_recipe(db, recipe_in)
    return RedirectResponse(url='/', status_code=303)


@app.get("/api/recipes")
def api_get_recipes(db: Session = Depends(get_db)):
    recipes = crud.get_recipes(db)
    out = []
    for r in recipes:
        out.append({
            "id": r.id,
            "name": r.name,
            "ingredients": json.loads(r.ingredients) if r.ingredients else [],
            "steps": json.loads(r.steps) if r.steps else [],
        })
    return out
