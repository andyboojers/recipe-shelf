from pydantic import BaseModel, Field
from typing import List, Optional

class BoundingBox(BaseModel):
    ymin: float
    xmin: float
    ymax: float
    xmax: float

class RecipeResponse(BaseModel):
    title: str = Field(..., description="The title of the recipe")
    ingredients: List[str] = Field(..., description="List of ingredients")
    instructions: List[str] = Field(..., description="Step by step instructions")
    notes: Optional[str] = Field(None, description="Additional notes")
    page_index: Optional[int] = Field(None, description="Index of the image containing the recipe")
    image_bounding_box: Optional[BoundingBox] = Field(None, description="Bounding box of the recipe image")

class ExtractionRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded string of the recipe image")

class ExtractionResponse(BaseModel):
    recipes: List[RecipeResponse]
