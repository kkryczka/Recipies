from typing import List, Optional
from pydantic import BaseModel
try:
    # Pydantic v2+: use ConfigDict
    from pydantic import ConfigDict
except Exception:
    ConfigDict = None


class RecipeBase(BaseModel):
    name: str
    ingredients: Optional[List[str]] = []
    steps: Optional[List[str]] = []


class RecipeCreate(RecipeBase):
    pass


class Recipe(RecipeBase):
    id: int

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True
