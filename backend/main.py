from fastapi import FastAPI
from schemas import ExtractionRequest, ExtractionResponse
from services.gemini_service import extract_recipes_from_images

app = FastAPI(title="Recipe Shelf API")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "recipe-shelf-backend"}

@app.post("/api/extract", response_model=ExtractionResponse)
def extract_recipe(request: ExtractionRequest):
    """
    Extracts recipes from an uploaded base64 image.
    """
    # The frontend currently sends a single base64 image
    image_parts = [{"mime_type": "image/jpeg", "data": request.image_data}]
    recipes = extract_recipes_from_images(image_parts)
    return ExtractionResponse(recipes=recipes)
