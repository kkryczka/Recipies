from typing import List, Optional
from pydantic import BaseModel, Field
try:
    # Pydantic v2+: use ConfigDict
    from pydantic import ConfigDict
except Exception:
    ConfigDict = None


class RecipeBase(BaseModel):
    name: str = Field(
        ..., json_schema_extra={"example": "Simple Pancakes"}
    )
    ingredients: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={"example": ["flour", "milk", "egg"]},
    )
    steps: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                "Mix dry ingredients",
                "Add wet ingredients",
                "Cook on skillet until golden",
            ]
        },
    )


class RecipeCreate(RecipeBase):
    pass


class Recipe(RecipeBase):
    id: int

    if ConfigDict is not None:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True
