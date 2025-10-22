import json
from sqlalchemy.orm import Session
from . import models, schemas


def get_recipe(db: Session, recipe_id: int):
    return db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()


def get_recipe_by_name(db: Session, name: str):
    return db.query(models.Recipe).filter(models.Recipe.name == name).first()


def get_recipes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Recipe).offset(skip).limit(limit).all()


def create_recipe(db: Session, recipe: schemas.RecipeCreate):
    db_recipe = models.Recipe(
        name=recipe.name,
        ingredients=json.dumps(recipe.ingredients or []),
        steps=json.dumps(recipe.steps or []),
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe(db: Session, recipe_id: int, recipe: schemas.RecipeCreate):
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return None
    db_recipe.name = recipe.name
    db_recipe.ingredients = json.dumps(recipe.ingredients or [])
    db_recipe.steps = json.dumps(recipe.steps or [])
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def delete_recipe(db: Session, recipe_id: int):
    db_recipe = get_recipe(db, recipe_id)
    if not db_recipe:
        return False
    db.delete(db_recipe)
    db.commit()
    return True
