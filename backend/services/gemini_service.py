import os
import json
import re
import google.generativeai as genai

def configure_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)

# Call on import to configure if env var is present
configure_gemini()

def extract_recipes_from_images(image_parts: list[dict]) -> dict:
    """
    Extracts recipes from a list of images using Gemini.
    
    Args:
        image_parts: list of dicts like [{"mime_type": "image/jpeg", "data": b"..."}]
    
    Returns:
        Dictionary with 'recipes' and 'detected_photos'.
    """
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json",
    }
    
    system_instruction = (
        "You are an expert recipe extractor. Identify every distinct recipe present across the provided images. "
        "For each recipe, extract the title, ingredients, instructions, and notes. "
        "Identify the bounding box of the main photograph for that recipe. "
        "Return a JSON object with two keys: "
        "'recipes' (a JSON array of objects representing the recipes), "
        "'detected_photos' (a JSON array of objects with 'page_index' (integer starting from 0 for the first image), 'ymin', 'xmin', 'ymax', 'xmax' representing the bounding boxes of EVERY distinct photograph of food on the pages. Coordinates are floats between 0.0 and 1.0 representing relative coordinates). "
        "For each recipe object, include: "
        "'title' (string), "
        "'ingredients' (list of strings), "
        "'instructions' (list of strings), "
        "'notes' (string), "
        "'servings' (string, e.g. '4 people' or '2-3 servings', or null if not found), "
        "'cooking_time' (string, total time required, or null if not found), "
        "'tags' (list of strings, automatically categorized based on ingredients/cuisine, e.g., ['dinner', 'vegetarian', 'pasta']). "
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    contents = image_parts + ["Extract the recipes."]
    
    try:
        response = model.generate_content(contents, request_options={"timeout": 120})
        
        text = response.text.strip()
        # Remove markdown code block syntax if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # In case there's still extra text, try to extract the outermost JSON object/array
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            text = match.group(1)
            
        data = json.loads(text)
        if isinstance(data, dict):
            recipes = data.get("recipes", [])
            photos = data.get("detected_photos", [])
            return {"recipes": recipes, "detected_photos": photos}
        elif isinstance(data, list):
            return {"recipes": data, "detected_photos": []}
        return {"recipes": [], "detected_photos": []}
    except Exception as e:
        print(f"Failed to parse Gemini response or API error: {e}")
        print(f"Raw response was: {response.text if 'response' in locals() else 'None'}")
        return {"recipes": [], "detected_photos": []}

def check_duplicate_recipe(new_recipe: dict, candidates: list[dict]) -> dict:
    """
    Evaluates if a new recipe is a duplicate of any candidate recipes using Gemini.
    """
    if not candidates:
        return {"is_duplicate": False, "duplicate_id": None}
        
    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json",
    }
    
    system_instruction = (
        "You are an expert culinary assistant. Your job is to determine if a newly submitted recipe is a semantic duplicate of any existing candidate recipes. "
        "Two recipes are duplicates if they are the exact same dish with highly similar ingredients, even if the wording or spelling differs slightly. "
        "Return a JSON object with two keys: "
        "'is_duplicate' (boolean, true if a semantic match is found), "
        "'duplicate_id' (string, the 'id' of the matching candidate recipe, or null if no match)."
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    prompt = f"New Recipe to check:\n{json.dumps(new_recipe, indent=2)}\n\nExisting Candidates:\n"
    for c in candidates:
        candidate_data = {
            "id": c.get("id"),
            "title": c.get("title"),
            "ingredients": c.get("ingredients")
        }
        prompt += f"{json.dumps(candidate_data, indent=2)}\n"
        
    try:
        response = model.generate_content(prompt, request_options={"timeout": 30})
        text = response.text.strip()
        # Clean markdown if present
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
            
        data = json.loads(text.strip())
        return {
            "is_duplicate": bool(data.get("is_duplicate", False)),
            "duplicate_id": data.get("duplicate_id")
        }
    except Exception as e:
        print(f"Failed to check duplicate with Gemini: {e}")
        return {"is_duplicate": False, "duplicate_id": None}
