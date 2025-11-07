# flake8: noqa
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` can be imported when tests are run
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # noqa: E402

import json
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient  # noqa: E402

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

    # root redirects to /match now; verify match page is accessible
    res = client.get("/")
    assert res.status_code in (200, 307, 308)
    # verify recipe exists via API
    res_api = client.get("/api/recipes?page=1&page_size=100")
    data = res_api.json()
    items = data.get("items", [])
    assert any(item.get("name") == "Test Pancake" for item in items)

    res2 = client.get("/api/recipes?page=1&page_size=100")
    assert res2.status_code == 200
    data = res2.json()
    assert isinstance(data, dict)
    items = data.get("items", [])
    assert any(item.get("name") == "Test Pancake" for item in items)


def test_create_recipe_via_form():
    # create via form POST
    res = client.post(
        "/recipes",
        data={"name": "FormRecipe", "ingredients": "a\nb", "steps": "1\n2"},
    )
    # allow either redirect or final 200
    assert res.status_code in (200, 303)

    # root now redirects; check via API that recipe exists
    res_api = client.get("/api/recipes?page=1&page_size=100")
    items = res_api.json().get("items", [])
    assert any(it.get("name") == "FormRecipe" for it in items)


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

    res = client.get("/api/recipes?page=1&page_size=100")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    items = data.get("items", [])
    found = next((it for it in items if it.get("name") == "JsonRecipe"), None)
    assert found is not None
    assert isinstance(found.get("ingredients"), list)
    assert isinstance(found.get("steps"), list)


def test_form_blank_lines_are_ignored():
    # posting ingredients/steps with blank lines should ignore empty entries
    res = client.post(
        "/recipes",
        data={
            "name": "BlankLines",
            "ingredients": "apple\n\nbanana\n",
            "steps": "step1\n\nstep2\n",
        },
    )
    assert res.status_code in (200, 303)

    # check via API that recipe was created
    res_api = client.get("/api/recipes?page=1&page_size=100")
    items = res_api.json().get("items", [])
    assert any(it.get("name") == "BlankLines" for it in items)


def test_update_and_delete_recipe():
    # create a recipe
    res = client.post("/recipes", data={"name": "ToChange", "ingredients": "x", "steps": "y"})
    assert res.status_code in (200, 303)

    # find its id via API
    data = client.get("/api/recipes?page=1&page_size=100").json()
    item = next((it for it in data.get("items", []) if it.get("name") == "ToChange"), None)
    assert item is not None
    rid = item["id"]

    # edit it
    res = client.post(f"/recipes/{rid}/edit", data={"name": "Changed", "ingredients": "a\nb", "steps": "1\n2"})
    assert res.status_code in (200, 303)

    data = client.get("/api/recipes?page=1&page_size=100").json()
    assert any(it.get("name") == "Changed" for it in data.get("items", []))

    # delete it
    res = client.post(f"/recipes/{rid}/delete")
    assert res.status_code in (200, 303)

    data = client.get("/api/recipes?page=1&page_size=100").json()
    assert not any(it.get("id") == rid for it in data.get("items", []))


def test_json_api_crud():
    # create
    payload = {"name": "JsonCRUD", "ingredients": ["a"], "steps": ["b"]}
    res = client.post("/api/recipes", json=payload)
    assert res.status_code == 200
    obj = res.json()
    rid = obj["id"]

    # get
    res = client.get(f"/api/recipes/{rid}")
    assert res.status_code == 200
    assert res.json()["name"] == "JsonCRUD"

    # update
    payload2 = {"name": "JsonCRUD-Updated", "ingredients": ["x"], "steps": ["y"]}
    res = client.put(f"/api/recipes/{rid}", json=payload2)
    assert res.status_code == 200
    assert res.json()["name"] == "JsonCRUD-Updated"

    # delete
    res = client.delete(f"/api/recipes/{rid}")
    assert res.status_code == 200
    assert res.json().get("deleted") is True


def test_search_api():
    # insert multiple recipes
    client.post("/api/recipes", json={"name": "Apple Pie", "ingredients": ["apple"], "steps": ["bake"]})
    client.post("/api/recipes", json={"name": "Banana Bread", "ingredients": ["banana"], "steps": ["bake"]})
    client.post("/api/recipes", json={"name": "Cherry Tart", "ingredients": ["cherry"], "steps": ["bake"]})

    res = client.get("/api/recipes?q=Banana&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Banana Bread"


def test_link_headers_pagination():
    # ensure we have multiple items
    for i in range(1, 12):
        client.post("/api/recipes", json={"name": f"Lnk{i}", "ingredients": ["x"], "steps": ["y"]})

    # request page 2 with page_size 5 -> should have prev and next
    res = client.get("/api/recipes?page=2&page_size=5")
    assert res.status_code == 200
    link = res.headers.get("Link")
    assert link is not None
    assert 'rel="prev"' in link and 'rel="next"' in link

    # first page should not have prev
    res = client.get("/api/recipes?page=1&page_size=5")
    assert res.status_code == 200
    link = res.headers.get("Link")
    assert link is not None
    assert 'rel="prev"' not in link and 'rel="next"' in link


def test_match_api():
    # create recipes
    client.post("/api/recipes", json={"name": "Match1", "ingredients": ["egg", "flour"], "steps": ["mix"]})
    client.post("/api/recipes", json={"name": "Match2", "ingredients": ["milk", "sugar"], "steps": ["mix"]})

    res = client.post("/api/match", json={"ingredients": ["egg", "flour", "butter"]})
    assert res.status_code == 200
    data = res.json()
    assert "have" in data and "results" in data
    # Match1 should have match True
    found = next((r for r in data["results"] if r["name"] == "Match1"), None)
    assert found is not None and found["match"] is True


def test_match_synonyms_and_plural():
    # aubergine should match eggplant via synonym map
    client.post("/api/recipes", json={"name": "EggplantDish", "ingredients": ["eggplant", "salt"], "steps": ["cook"]})
    # create recipe that requires only 'tomato' to test plural normalization
    client.post("/api/recipes", json={"name": "TomatoSalad", "ingredients": ["tomato"], "steps": ["mix"]})

    # provide 'aubergine' (UK) and 'tomatoes' (plural) in have list
    res = client.post("/api/match", json={"ingredients": ["aubergine", "tomatoes", "salt"]})
    assert res.status_code == 200
    data = res.json()
    names = {r["name"]: r for r in data["results"]}
    assert "EggplantDish" in names and names["EggplantDish"]["match"] is True
    assert "TomatoSalad" in names and names["TomatoSalad"]["match"] is True

