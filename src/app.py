# flake8: noqa

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import json

from . import crud, schemas
from .db import SessionLocal, init_db
from typing import List
from .normalize import normalize_ingredient, is_ingredient_match
from .translate import translate_list, translate_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB once at startup
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Serve static assets (logo, css, js) using absolute path so reloads work
static_dir = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")




# Serve a small favicon to avoid 404 noise from browsers requesting /favicon.ico
@app.get("/favicon.ico")
def favicon():
    fav = static_dir / "img" / "favicon.ico"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/x-icon")
    # fallback: return a 204 No Content-like empty response using a small transparent svg
    empty_svg = "<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'></svg>"
    return HTMLResponse(content=empty_svg, media_type="image/svg+xml")

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


@app.get('/my-recipes')
def my_recipes():
    raise HTTPException(status_code=501, detail='Not implemented in wireframe')


@app.get('/favorites')
def favorites():
    raise HTTPException(status_code=501, detail='Not implemented in wireframe')


@app.get('/profile')
def profile():
    raise HTTPException(status_code=501, detail='Not implemented in wireframe')


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    # Serve match UI at root and show some recipes from the DB as demo tiles
    recipes = crud.get_recipes(db, skip=0, limit=12)
    results = []
    for r in recipes:
        results.append({
            "id": r.id,
            "name": r.name,
            "matched_count": 0,
            "matched": [],
            "match": True,
            "missing_count": 0,
            "missing": [],
        })
    return templates.TemplateResponse(
        request,
        "match.html",
        {"have_text": "", "results": {"have": [], "results": results}},
    )


@app.post('/match', response_class=HTMLResponse)
def match_post(request: Request, ingredients: str = Form(''), db: Session = Depends(get_db)):
    # Receive newline-separated ingredients from the hidden textarea
    have_text = ingredients or ''
    have_list = [normalize_ingredient(x) for x in have_text.split('\n') if x and x.strip()]
    have_set = set([h for h in have_list if h])

    # Simple exact-match demo: mark recipes that have ingredients fully satisfied by `have_set`.
    recipes = crud.get_recipes(db, skip=0, limit=50)
    results = []
    for r in recipes:
        try:
            ings = json.loads(r.ingredients or '[]')
        except Exception:
            ings = []
        norm_ings = [normalize_ingredient(i) for i in ings if i]
        matched = [i for i in norm_ings if i in have_set]
        missing = [i for i in norm_ings if i not in have_set]
        results.append({
            "id": r.id,
            "name": r.name,
            "matched_count": len(matched),
            "matched": matched,
            "match": len(missing) == 0,
            "missing_count": len(missing),
            "missing": missing,
        })

    return templates.TemplateResponse(request, 'match.html', {"have_text": have_text, "results": {"have": have_list, "results": results}})


@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def view_recipe(
    request: Request, recipe_id: int, lang: str | None = None, db: Session = Depends(get_db)
):
    r = crud.get_recipe(db, recipe_id)
    if not r:
        # Render a demo/detail page when recipe is missing so wireframe clicks always display something
        demo_ings = ["ingredient A", "ingredient B", "ingredient C"]
        demo_steps = ["Step 1: Prep", "Step 2: Cook", "Step 3: Serve"]
        t_ings = translate_list(demo_ings, lang) if lang else demo_ings
        t_steps = translate_list(demo_steps, lang) if lang else demo_steps
        recipe = {"id": recipe_id, "name": f"Demo Recipe {recipe_id}", "ingredients": t_ings, "steps": t_steps}
    else:
        ings = json.loads(r.ingredients or '[]')
        steps = json.loads(r.steps or '[]')
        # translate if lang provided
        t_ings = translate_list(ings, lang) if lang else ings
        t_steps = translate_list(steps, lang) if lang else steps
        recipe = {"id": r.id, "name": r.name, "ingredients": t_ings, "steps": t_steps}
    heading_ingredients = translate_text("Ingredients", lang) if lang else "Ingredients"
    heading_steps = translate_text("Steps", lang) if lang else "Steps"
    back_label = translate_text("Back", lang) if lang else "Back"
    edit_label = translate_text("Edit", lang) if lang else "Edit"
    delete_label = translate_text("Delete", lang) if lang else "Delete"
    # For wireframe/demo mode return JSON so clicking a tile shows recipe data.
    return JSONResponse(content=recipe)


@app.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def edit_recipe_form(
    request: Request, recipe_id: int, db: Session = Depends(get_db)
):
    r = crud.get_recipe(db, recipe_id)
    if not r:
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse
        from fastapi.templating import Jinja2Templates
        from fastapi.staticfiles import StaticFiles
        from pathlib import Path
        from contextlib import asynccontextmanager


        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Minimal app for wireframe prototype; no DB initialization
            yield


        app = FastAPI(lifespan=lifespan)
        templates = Jinja2Templates(directory="templates")

        # Serve static assets from the project static directory
        static_dir = Path(__file__).resolve().parents[1] / "static"
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


        @app.get("/", response_class=HTMLResponse)
        def read_root(request: Request, q: str | None = None):
            # Render the wireframe-first match page. Keep have_text optional for demo.
            have_text = q or ""
            return templates.TemplateResponse(request, "match.html", {"have_text": have_text})

