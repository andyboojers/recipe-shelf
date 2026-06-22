from dotenv import load_dotenv
load_dotenv()

import os
from pillow_heif import register_heif_opener
register_heif_opener()

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
from services.drive_service import save_recipe_to_drive, delete_recipe_folder
from services.cache_service import get_image_file
from database import (
    save_draft, get_draft, delete_draft, 
    save_recipe_cache, get_recipe, delete_recipe, search_recipes, init_db
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
        # Pre-process: Convert any HEIC/HEIF images to JPEG
        for img in request.images:
            mime = img.mime_type or "image/jpeg"
            if mime.lower() in ["image/heic", "image/heif"]:
                try:
                    img_bytes = base64.b64decode(img.image_data)
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    
                    # Convert color space to RGB (HEIC can be CMYK or other formats) and save as JPEG
                    buffered = io.BytesIO()
                    pil_img.convert("RGB").save(buffered, format="JPEG", quality=90)
                    
                    img.image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    img.mime_type = "image/jpeg"
                    print("Successfully converted HEIC/HEIF image to JPEG")
                except Exception as e:
                    print(f"Warning: Failed to convert HEIC/HEIF to JPEG: {e}")

        image_parts = [{"mime_type": img.mime_type or "image/jpeg", "data": img.image_data} for img in request.images]
        gemini_result = extract_recipes_from_images(image_parts)
        recipes = gemini_result.get("recipes") or []
        photos = gemini_result.get("detected_photos") or []
        
        candidate_images = []
        if photos:
            try:
                # Decode original images to extract candidate thumbnails matching correct page_index
                loaded_images = {}
                for box in photos:
                    page_index = box.get("page_index", 0)
                    if page_index >= len(request.images):
                        continue
                        
                    if page_index not in loaded_images:
                        img_data = request.images[page_index]
                        if img_data.mime_type == "application/pdf":
                            continue
                        img_bytes = base64.b64decode(img_data.image_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        img = ImageOps.exif_transpose(img)
                        loaded_images[page_index] = img
                    
                    img = loaded_images[page_index]
                    width, height = img.size
                    
                    xmin = box.get("xmin", 0)
                    ymin = box.get("ymin", 0)
                    xmax = box.get("xmax", 1)
                    ymax = box.get("ymax", 1)

                    if xmax > 1.0 or ymax > 1.0 or xmin > 1.0 or ymin > 1.0:
                        xmin /= 1000.0
                        ymin /= 1000.0
                        xmax /= 1000.0
                        ymax /= 1000.0

                    left = int(xmin * width)
                    top = int(ymin * height)
                    right = int(xmax * width)
                    bottom = int(ymax * height)
                    
                    cropped = img.crop((left, top, right, bottom))
                    cropped.thumbnail((400, 400)) # Resize to save bandwidth
                    
                    buffered = io.BytesIO()
                    cropped.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    candidate_images.append(img_str)
            except Exception as e:
                print(f"Error cropping images: {e}")
    
        draft_ids = []
        # Save original scans for this extraction
        from database import DATA_DIR
        import os
        
        # We will share these original scans across all drafted recipes
        for recipe in recipes:
            if not isinstance(recipe, dict):
                continue
                
            draft_id = str(uuid.uuid4())
            
            # Save all original scans for this draft
            original_paths = []
            for idx, img_data in enumerate(request.images):
                img_bytes = base64.b64decode(img_data.image_data)
                original_path = os.path.join(DATA_DIR, "drafts", f"{draft_id}_original_{idx}.jpg")
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                with open(original_path, "wb") as f:
                    f.write(img_bytes)
                original_paths.append(original_path)
                
            save_draft(
                draft_id=draft_id,
                title=recipe.get("title", "Untitled Recipe"),
                ingredients=recipe.get("ingredients", []),
                instructions=recipe.get("instructions", []),
                notes=recipe.get("notes", ""),
                servings=recipe.get("servings", ""),
                cooking_time=recipe.get("cooking_time", ""),
                tags=recipe.get("tags", []),
                image_path="",
                original_image_paths=original_paths
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
            image_path=file_path,
            original_image_paths=draft.get("original_image_paths", [])
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

@app.get("/api/drafts/{draft_id}/original-image")
def get_draft_original_image(draft_id: str, page: int = 0):
    import os
    from database import DATA_DIR
    
    file_path = os.path.join(DATA_DIR, "drafts", f"{draft_id}_original_{page}.jpg")
    # Fallback to older format if not found
    if not os.path.exists(file_path):
        file_path = os.path.join(DATA_DIR, "drafts", f"{draft_id}_original.jpg")
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original image not found")
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
        
    if not request.force_save:
        from database import find_candidate_duplicates
        from services.gemini_service import check_duplicate_recipe
        candidates = find_candidate_duplicates(request.title, limit=5)
        if candidates:
            new_recipe_data = {"title": request.title, "ingredients": request.ingredients}
            duplicate_check = check_duplicate_recipe(new_recipe_data, candidates)
            if duplicate_check.get("is_duplicate"):
                dup_id = duplicate_check.get("duplicate_id")
                dup_title = next((c["title"] for c in candidates if c["id"] == dup_id), "an existing recipe")
                raise HTTPException(
                    status_code=409,
                    detail={
                        "duplicate_detected": True,
                        "duplicate_id": dup_id,
                        "duplicate_title": dup_title,
                        "message": f"This looks very similar to your existing recipe: '{dup_title}'. Do you still want to save it as a new recipe?"
                    }
                )
    
    
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
    
    try:
        drive_file_id, image_drive_id, original_drive_ids = save_recipe_to_drive(
            recipe_id, 
            recipe_data, 
            draft.get("image_path"), 
            draft.get("original_image_paths", [])
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Google Drive Save Failed: {str(e)}"
        )
    
    try:
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
            image_drive_id=image_drive_id,
            original_drive_ids=original_drive_ids
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Local Cache Save Failed: {str(e)}"
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

@app.delete("/api/recipes/{recipe_id}")
def delete_recipe_endpoint(recipe_id: str):
    recipe = get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    try:
        if recipe.get("drive_file_id"):
            delete_recipe_folder(recipe["drive_file_id"])
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Warning: Failed to delete recipe folder from drive: {e}")
        
    delete_recipe(recipe_id)
    return {"status": "success", "message": "Recipe deleted"}


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

@app.get("/api/files/{drive_file_id:path}")
def get_file_endpoint(drive_file_id: str):
    try:
        file_path = get_image_file(drive_file_id)
        return FileResponse(file_path, media_type="image/jpeg")
    except Exception as e:
        print(f"Error serving file {drive_file_id}: {e}")
        try:
            # Generate a simple fallback placeholder image using PIL
            from PIL import Image
            import io
            img = Image.new('RGB', (300, 300), color = (220, 220, 220))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            return Response(content=img_byte_arr.getvalue(), media_type="image/jpeg")
        except Exception:
            raise HTTPException(status_code=404, detail="File not found")
