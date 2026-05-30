from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from schemas import (
    ExtractionRequest, ExtractionResponse, DraftResponse, 
    RecipeSaveRequest, RecipeSearchResponse, RecipeMetadata,
    DraftImageAttachRequest
)
import io
import base64
from PIL import Image, ImageOps
from services.gemini_service import extract_recipes_from_images
from services.drive_service import save_recipe_to_drive
from database import (
    save_draft, get_draft, delete_draft, 
    save_recipe_cache, get_recipe, search_recipes, init_db
)
import uuid

# Initialize database tables on startup
init_db()

app = FastAPI(title="Recipe Shelf API")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "recipe-shelf-backend"}

@app.post("/api/extract", response_model=ExtractionResponse)
def extract_recipe(request: ExtractionRequest):
    """
    Extracts recipes from an uploaded base64 image and saves them as drafts.
    """
    try:
        image_parts = [{"mime_type": "image/jpeg", "data": request.image_data}]
        gemini_result = extract_recipes_from_images(image_parts)
        recipes = gemini_result.get("recipes") or []
        photos = gemini_result.get("detected_photos") or []
        
        candidate_images = []
        if photos:
            try:
                # Decode the original image
                img_bytes = base64.b64decode(request.image_data)
                img = Image.open(io.BytesIO(img_bytes))
                img = ImageOps.exif_transpose(img)
                width, height = img.size
                
                for box in photos:
                    # box has ymin, xmin, ymax, xmax (relative 0.0-1.0)
                    left = int(box.get("xmin", 0) * width)
                    top = int(box.get("ymin", 0) * height)
                    right = int(box.get("xmax", 1) * width)
                    bottom = int(box.get("ymax", 1) * height)
                    
                    cropped = img.crop((left, top, right, bottom))
                    cropped.thumbnail((400, 400)) # Resize to save bandwidth
                    
                    buffered = io.BytesIO()
                    cropped.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    candidate_images.append(img_str)
            except Exception as e:
                print(f"Error cropping images: {e}")
    
        draft_ids = []
        # If the mock returns a list of dictionaries, we access with .get()
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
                
            draft_id = str(uuid.uuid4())
            save_draft(
                draft_id=draft_id,
                title=recipe.get("title", "Untitled Recipe"),
                ingredients=recipe.get("ingredients", []),
                instructions=recipe.get("instructions", []),
                notes=recipe.get("notes", ""),
                servings=recipe.get("servings", ""),
                cooking_time=recipe.get("cooking_time", ""),
                tags=recipe.get("tags", []),
                image_path=""
            )
            draft_ids.append(draft_id)
            
        return ExtractionResponse(draft_ids=draft_ids, candidate_images=candidate_images)
    except Exception as e:
        print(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/drafts/{draft_id}/image")
def attach_draft_image(draft_id: str, request: DraftImageAttachRequest):
    draft = get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    try:
        import os
        from database import DATA_DIR
        
        img_bytes = base64.b64decode(request.image_data)
        file_path = os.path.join(DATA_DIR, "drafts", f"{draft_id}.jpg")
        with open(file_path, "wb") as f:
            f.write(img_bytes)
            
        save_draft(
            draft_id=draft["id"],
            title=draft["title"],
            ingredients=draft["ingredients"],
            instructions=draft["instructions"],
            notes=draft["notes"],
            servings=draft.get("servings", ""),
            cooking_time=draft.get("cooking_time", ""),
            tags=draft.get("tags", []),
            image_path=file_path
        )
        return {"status": "success", "image_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drafts/{draft_id}/image")
def get_draft_image(draft_id: str):
    import os
    from database import DATA_DIR
    
    file_path = os.path.join(DATA_DIR, "drafts", f"{draft_id}.jpg")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@app.get("/api/drafts/{draft_id}", response_model=DraftResponse)
def get_draft_endpoint(draft_id: str):
    draft = get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return DraftResponse(**draft)

@app.post("/api/recipes")
def save_recipe_endpoint(request: RecipeSaveRequest):
    draft = get_draft(request.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    recipe_id = str(uuid.uuid4())
    recipe_data = {
        "title": request.title,
        "ingredients": request.ingredients,
        "instructions": request.instructions,
        "notes": request.notes,
        "servings": request.servings,
        "cooking_time": request.cooking_time,
        "tags": request.tags
    }
    
    drive_file_id, image_drive_id = save_recipe_to_drive(recipe_id, recipe_data, draft.get("image_path"))
    
    save_recipe_cache(
        recipe_id=recipe_id,
        title=request.title,
        ingredients=request.ingredients,
        instructions=request.instructions,
        notes=request.notes or "",
        servings=request.servings or "",
        cooking_time=request.cooking_time or "",
        tags=request.tags or [],
        drive_file_id=drive_file_id,
        image_drive_id=image_drive_id
    )
    
    delete_draft(request.draft_id)
    return {"status": "success", "recipe_id": recipe_id}

@app.get("/api/recipes", response_model=RecipeSearchResponse)
def search_recipes_endpoint(q: str = ""):
    results = search_recipes(q)
    return RecipeSearchResponse(results=results)

@app.get("/api/recipes/{recipe_id}", response_model=RecipeMetadata)
def get_recipe_endpoint(recipe_id: str):
    recipe = get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeMetadata(**recipe)

from schemas import RecipeUpdateRequest

@app.put("/api/recipes/{recipe_id}")
def update_recipe_endpoint(recipe_id: str, request: RecipeUpdateRequest):
    recipe = get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # In a real app, update the file in Drive here. For now, update cache.
    save_recipe_cache(
        recipe_id=recipe_id,
        title=request.title,
        ingredients=request.ingredients,
        instructions=request.instructions,
        notes=request.notes or "",
        servings=request.servings or "",
        cooking_time=request.cooking_time or "",
        tags=request.tags or [],
        drive_file_id=recipe["drive_file_id"],
        image_drive_id=recipe["image_drive_id"]
    )
    return {"status": "success", "recipe_id": recipe_id}

from fastapi.responses import Response, FileResponse

@app.get("/api/files/{drive_file_id}")
def get_file_endpoint(drive_file_id: str):
    # Mocking the image stream from drive for MVP
    return Response(content=b"dummy_image_data", media_type="image/jpeg")
