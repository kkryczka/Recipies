from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import json

from . import crud, models, schemas
from .db import SessionLocal, init_db
from typing import List
from .normalize import normalize_ingredient, is_ingredient_match


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB once at startup
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Allow CORS for API clients (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, page: int = 1, page_size: int = 5, db: Session = Depends(get_db)):
    # pagination
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    skip = (page - 1) * page_size
    total = crud.count_recipes(db)
    recipes = crud.get_recipes(db, skip=skip, limit=page_size)
    # decode JSON fields for template
    out = []
    for r in recipes:
        out.append({
            "id": r.id,
            "name": r.name,
            "ingredients": json.loads(r.ingredients) if r.ingredients else [],
            "steps": json.loads(r.steps) if r.steps else [],
        })
    pages = (total + page_size - 1) // page_size
    return templates.TemplateResponse(request, "index.html", {"recipes": out, "page": page, "pages": pages})


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
def api_get_recipes(request: Request, page: int = 1, page_size: int = 10, q: str | None = None, db: Session = Depends(get_db)):
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    skip = (page - 1) * page_size
    total = crud.count_recipes_filtered(db, q)
    recipes = crud.search_recipes(db, q=q, skip=skip, limit=page_size)
    out = []
    for r in recipes:
        out.append({
            "id": r.id,
            "name": r.name,
            "ingredients": json.loads(r.ingredients) if r.ingredients else [],
            "steps": json.loads(r.steps) if r.steps else [],
        })
    # build RFC5988 Link header
    last_page = (total + page_size - 1) // page_size if total > 0 else 1
    links = []
    base = str(request.url.include_query_params())
    # helper to build url with page param
    def url_for(p):
        return str(request.url.include_query_params(page=p, page_size=page_size, q=q))

    if page > 1:
        links.append(f"<{url_for(1)}>; rel=\"first\"")
        links.append(f"<{url_for(page-1)}>; rel=\"prev\"")
    if page < last_page:
        links.append(f"<{url_for(page+1)}>; rel=\"next\"")
        links.append(f"<{url_for(last_page)}>; rel=\"last\"")

    headers = {}
    if links:
        headers["Link"] = ", ".join(links)

    payload = {"page": page, "page_size": page_size, "total": total, "items": out}
    return JSONResponse(content=payload, headers=headers)


@app.post(
    "/api/recipes",
    response_model=schemas.Recipe,
    responses={200: {"description": "Recipe created"}},
    summary="Create a recipe",
    description="Create a new recipe via JSON payload",
)
def api_create_recipe(recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    existing = crud.get_recipe_by_name(db, recipe.name)
    if existing:
        raise HTTPException(status_code=400, detail="Recipe with that name already exists")
    r = crud.create_recipe(db, recipe)
    return {"id": r.id, "name": r.name, "ingredients": json.loads(r.ingredients or '[]'), "steps": json.loads(r.steps or '[]')}


@app.get("/api/recipes/{recipe_id}", response_model=schemas.Recipe)
def api_get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    r = crud.get_recipe(db, recipe_id)
    if not r:
        raise HTTPException(status_code=404)
    return {"id": r.id, "name": r.name, "ingredients": json.loads(r.ingredients or '[]'), "steps": json.loads(r.steps or '[]')}


@app.put(
    "/api/recipes/{recipe_id}",
    response_model=schemas.Recipe,
    summary="Update a recipe",
    description="Update recipe by id with JSON payload",
)
def api_update_recipe(recipe_id: int, recipe: schemas.RecipeCreate, db: Session = Depends(get_db)):
    updated = crud.update_recipe(db, recipe_id, recipe)
    if not updated:
        raise HTTPException(status_code=404)
    return {"id": updated.id, "name": updated.name, "ingredients": json.loads(updated.ingredients or '[]'), "steps": json.loads(updated.steps or '[]')}


@app.delete("/api/recipes/{recipe_id}")
def api_delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_recipe(db, recipe_id)
    if not ok:
        raise HTTPException(status_code=404)
    return {"deleted": True}


def _normalize_ings(ings: List[str]) -> set:
    return {normalize_ingredient(i) for i in (ings or []) if i and i.strip()}


@app.post("/api/match")
def api_match(payload: dict, db: Session = Depends(get_db)):
    # payload: { "ingredients": ["flour", "milk"] }
    ings = payload.get("ingredients") if isinstance(payload, dict) else None
    if not isinstance(ings, list):
        raise HTTPException(status_code=400, detail="'ingredients' must be a list of strings")
    have = _normalize_ings(ings)
    results = []
    all_recipes = crud.get_recipes(db, skip=0, limit=1000)
    for r in all_recipes:
        r_ings = json.loads(r.ingredients) if r.ingredients else []
        missing = []
        for i in r_ings:
            if not is_ingredient_match(i, have):
                missing.append(i)
        results.append({"id": r.id, "name": r.name, "missing": missing, "missing_count": len(missing), "match": len(missing) == 0})
    # sort with matches first then by missing count and name
    results.sort(key=lambda x: (0 if x["match"] else 1, x["missing_count"], x["name"]))
    return {"have": sorted(list(have)), "results": results}


@app.get("/match", response_class=HTMLResponse)
def match_form(request: Request):
    return templates.TemplateResponse(request, "match.html", {"have_text": "", "results": None})


@app.post("/match", response_class=HTMLResponse)
def match_submit(request: Request, ingredients: str = Form(""), db: Session = Depends(get_db)):
    # ingredients provided one-per-line
    lines = [l.strip() for l in ingredients.splitlines() if l.strip()]
    payload = {"ingredients": lines}
    resp = api_match(payload, db)
    return templates.TemplateResponse(request, "match.html", {"have_text": ingredients, "results": resp})
