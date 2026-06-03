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
    servings: Optional[str] = Field(None, description="Number of servings")
    cooking_time: Optional[str] = Field(None, description="Total cooking time")
    tags: List[str] = Field(default_factory=list, description="Tags automatically assigned")
    page_index: Optional[int] = Field(None, description="Index of the image containing the recipe")
    image_bounding_box: Optional[BoundingBox] = Field(None, description="Bounding box of the recipe image")

class ExtractionRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded string of the recipe image")
    mime_type: Optional[str] = Field("image/jpeg", description="MIME type of the uploaded file")

class ExtractionResponse(BaseModel):
    draft_ids: List[str]
    candidate_images: List[str] = Field(default_factory=list)

class DraftResponse(BaseModel):
    id: str
    title: str
    ingredients: List[str]
    instructions: List[str]
    notes: Optional[str]
    servings: Optional[str] = None
    cooking_time: Optional[str] = None
    tags: List[str] = []
    image_path: Optional[str]

class DraftImageAttachRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded string of the cropped thumbnail image")

class RecipeSaveRequest(BaseModel):
    draft_id: str
    title: str
    ingredients: List[str]
    instructions: List[str]
    notes: Optional[str]
    servings: Optional[str] = None
    cooking_time: Optional[str] = None
    tags: List[str] = []

class RecipeUpdateRequest(BaseModel):
    title: str
    ingredients: List[str]
    instructions: List[str]
    notes: Optional[str]
    servings: Optional[str] = None
    cooking_time: Optional[str] = None
    tags: List[str] = []

class RecipeMetadata(BaseModel):
    id: str
    title: str
    ingredients: List[str]
    instructions: List[str]
    notes: Optional[str]
    servings: Optional[str] = None
    cooking_time: Optional[str] = None
    tags: List[str] = []
    drive_file_id: Optional[str]
    image_drive_id: Optional[str]
    last_updated: Optional[str]

class RecipeSearchResponse(BaseModel):
    results: List[RecipeMetadata]
