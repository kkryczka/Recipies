import json
from pathlib import Path

from src.db import init_db, SessionLocal
from src import models


def main():
    init_db()
    p = Path(__file__).resolve().parents[1] / 'data' / 'recipes.json'
    if not p.exists():
        print('data/recipes.json not found')
        return
    data = json.loads(p.read_text(encoding='utf-8'))
    db = SessionLocal()
    added = 0
    for r in data:
        name = r.get('name')
        if not name:
            continue
        exists = (
            db.query(models.Recipe)
            .filter(models.Recipe.name == name)
            .first()
        )
        if exists:
            continue
        recipe = models.Recipe(
            name=name,
            ingredients=json.dumps(r.get('ingredients', [])),
            steps=json.dumps(r.get('steps', [])),
        )
        db.add(recipe)
        added += 1
    db.commit()
    db.close()
    print(f'Imported {added} recipes')


if __name__ == '__main__':
    main()
