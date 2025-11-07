# flake8: noqa
import sys
from pathlib import Path
from fastapi.testclient import TestClient  # noqa: E402

# Ensure project root is on sys.path so `src` can be imported when tests are run
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # noqa: E402
from src import app as app_module


client = TestClient(app_module.app)


def test_view_translation_polish():
    # create a recipe via API
    res = client.post("/api/recipes", json={"name": "PlTest", "ingredients": ["tomato", "salt"], "steps": ["mix", "serve"]})
    assert res.status_code == 200
    obj = res.json()
    rid = obj["id"]

    res = client.get(f"/recipes/{rid}?lang=pl")
    assert res.status_code == 200
    text = res.text
    # check Polish translations for heading and a known ingredient
    assert "Składniki" in text
    assert "pomidor" in text
