import os
import json
import google.generativeai as genai

def configure_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)

# Call on import to configure if env var is present
configure_gemini()

def extract_recipes_from_images(image_parts: list[dict]) -> list[dict]:
    """
    Extracts recipes from a list of images using Gemini.
    
    Args:
        image_parts: list of dicts like [{"mime_type": "image/jpeg", "data": b"..."}]
    
    Returns:
        List of recipe dictionaries.
    """
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json",
    }
    
    system_instruction = (
        "You are an expert recipe extractor. Identify every distinct recipe present across the provided images. "
        "For each recipe, extract the title, ingredients, instructions, and notes. "
        "Identify the bounding box of the main photograph for that recipe. "
        "Return a JSON array of objects with keys: "
        "'title' (string), "
        "'ingredients' (list of strings), "
        "'instructions' (list of strings), "
        "'notes' (string), "
        "'page_index' (integer, 0-indexed referring to the image containing the recipe's main photograph), "
        "'image_bounding_box' (object with 'ymin', 'xmin', 'ymax', 'xmax' as floats between 0.0 and 1.0 representing relative coordinates). "
        "If a recipe does not have an image, set image_bounding_box to null."
    )
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    contents = image_parts + ["Extract the recipes."]
    
    try:
        response = model.generate_content(contents)
        data = json.loads(response.text)
        if isinstance(data, dict) and "recipes" in data:
            return data["recipes"]
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"Failed to parse Gemini response or API error: {e}")
        return []
