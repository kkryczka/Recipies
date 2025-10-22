import json
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

# Ensure project root is on sys.path so `src` can be imported when tests are run
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src import app as app_module
from src import models


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
# Use StaticPool so the same in-memory database is shared across connections
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the in-memory database
models.Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app_module.app.dependency_overrides[app_module.get_db] = override_get_db
client = TestClient(app_module.app)


def test_root_and_api_list():
    # insert a recipe directly into the test DB
    db = TestingSessionLocal()
    r = models.Recipe(name="Test Pancake", ingredients=json.dumps(["flour", "egg"]), steps=json.dumps(["mix", "cook"]))
    db.add(r)
    db.commit()
    db.close()

    res = client.get("/")
    assert res.status_code == 200
    assert "Test Pancake" in res.text

    res2 = client.get("/api/recipes")
    assert res2.status_code == 200
    data = res2.json()
    assert isinstance(data, list)
    assert any(item.get("name") == "Test Pancake" for item in data)


def test_create_recipe_via_form():
    # create via form POST
    res = client.post("/recipes", data={"name": "FormRecipe", "ingredients": "a\nb", "steps": "1\n2"})
    # allow either redirect or final 200
    assert res.status_code in (200, 303)

    res = client.get("/")
    assert "FormRecipe" in res.text


def test_duplicate_recipe_name():
    # create recipe
    res1 = client.post("/recipes", data={"name": "DupRecipe", "ingredients": "i1", "steps": "s1"})
    assert res1.status_code in (200, 303)

    # second create with same name should return 400
    res2 = client.post("/recipes", data={"name": "DupRecipe", "ingredients": "i2", "steps": "s2"})
    assert res2.status_code == 400


def test_missing_name_validation():
    # name is required in the form -> expect 422 Unprocessable Entity
    res = client.post("/recipes", data={"ingredients": "a\nb", "steps": "1\n2"})
    assert res.status_code == 422


def test_api_json_structure():
    # insert a recipe directly into the test DB
    db = TestingSessionLocal()
    r = models.Recipe(name="JsonRecipe", ingredients=json.dumps(["salt", "pepper"]), steps=json.dumps(["mix"]))
    db.add(r)
    db.commit()
    db.close()

    res = client.get("/api/recipes")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    found = next((it for it in data if it.get("name") == "JsonRecipe"), None)
    assert found is not None
    assert isinstance(found.get("ingredients"), list)
    assert isinstance(found.get("steps"), list)


def test_form_blank_lines_are_ignored():
    # posting ingredients/steps with blank lines should ignore empty entries
    res = client.post("/recipes", data={"name": "BlankLines", "ingredients": "apple\n\nbanana\n", "steps": "step1\n\nstep2\n"})
    assert res.status_code in (200, 303)

    res = client.get("/")
    assert "BlankLines" in res.text
    # ensure no empty list items appear (simple check: no consecutive <li> with nothing)
    assert "<li></li>" not in res.text


def test_update_and_delete_recipe():
    # create a recipe
    res = client.post("/recipes", data={"name": "ToChange", "ingredients": "x", "steps": "y"})
    assert res.status_code in (200, 303)

    # find its id via API
    data = client.get("/api/recipes").json()
    item = next((it for it in data if it.get("name") == "ToChange"), None)
    assert item is not None
    rid = item["id"]

    # edit it
    res = client.post(f"/recipes/{rid}/edit", data={"name": "Changed", "ingredients": "a\nb", "steps": "1\n2"})
    assert res.status_code in (200, 303)

    data = client.get("/api/recipes").json()
    assert any(it.get("name") == "Changed" for it in data)

    # delete it
    res = client.post(f"/recipes/{rid}/delete")
    assert res.status_code in (200, 303)

    data = client.get("/api/recipes").json()
    assert not any(it.get("id") == rid for it in data)
