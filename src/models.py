from sqlalchemy import Column, Integer, String, Text
# relationship not used; models are simple
from .db import Base


class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    ingredients = Column(Text, nullable=True)  # JSON-encoded list
    steps = Column(Text, nullable=True)  # JSON-encoded list
