import json
from pathlib import Path


def load_recipes(path):
    """Load recipes from a JSON file and return a list of dicts.

    Args:
        path (str or Path): Path to the JSON file.

    Returns:
        list: list of recipe dictionaries.
    """
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
