import os
import json
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
        "'detected_photos' (a JSON array of objects with 'ymin', 'xmin', 'ymax', 'xmax' representing the bounding boxes of EVERY distinct photograph of food on the page, as floats between 0.0 and 1.0 representing relative coordinates). "
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
        model_name="gemini-flash-latest",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    contents = image_parts + ["Extract the recipes."]
    
    try:
        response = model.generate_content(contents)
        data = json.loads(response.text)
        if isinstance(data, dict):
            recipes = data.get("recipes", [])
            photos = data.get("detected_photos", [])
            return {"recipes": recipes, "detected_photos": photos}
        elif isinstance(data, list):
            return {"recipes": data, "detected_photos": []}
        return {"recipes": [], "detected_photos": []}
    except Exception as e:
        print(f"Failed to parse Gemini response or API error: {e}")
        return {"recipes": [], "detected_photos": []}
