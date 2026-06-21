import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_parse_gemini_response_success():
    """Unit test: parsing a valid gemini string response."""
    # We no longer test parse_gemini_response as the SDK handles JSON returning in the new gemini_service.py
    pass

def test_extract_endpoint_success(mocker):
    """Functional test: POST /api/extract with mocked Gemini service."""
    mocker.patch("main.extract_recipes_from_images", return_value={"recipes": [{
        "title": "Mocked Recipe 1",
        "ingredients": ["Mock ingredient"],
        "instructions": ["Mock instruction"],
        "notes": "Mock note",
        "servings": "4",
        "cooking_time": "30m",
        "tags": ["mock"],
        "page_index": 0,
        "image_bounding_box": {"ymin": 0.1, "xmin": 0.1, "ymax": 0.9, "xmax": 0.9}
    }], "detected_photos": []})
    
    response = client.post(
        "/api/extract",
        json={"images": [{"image_data": "base64_encoded_dummy_string", "mime_type": "image/jpeg"}]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["draft_ids"]) == 1
    draft_id = data["draft_ids"][0]
    
    # Verify draft was created
    draft_resp = client.get(f"/api/drafts/{draft_id}")
    assert draft_resp.status_code == 200
    assert draft_resp.json()["title"] == "Mocked Recipe 1"

def test_extract_endpoint_heic_conversion(mocker):
    """Test that POST /api/extract converts incoming HEIC images to JPEG."""
    import base64
    import os
    from PIL import Image
    
    heic_path = os.path.join(os.path.dirname(__file__), "test.heic")
    assert os.path.exists(heic_path), f"Test HEIC file is missing at {heic_path}"
    
    with open(heic_path, "rb") as f:
        heic_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    mocker.patch("main.extract_recipes_from_images", return_value={"recipes": [{
        "title": "HEIC Converted Recipe",
        "ingredients": [],
        "instructions": [],
        "notes": "",
        "servings": "",
        "cooking_time": "",
        "tags": []
    }], "detected_photos": []})
    
    response = client.post(
        "/api/extract",
        json={"images": [{"image_data": heic_b64, "mime_type": "image/heic"}]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["draft_ids"]) == 1
    draft_id = data["draft_ids"][0]
    
    draft_resp = client.get(f"/api/drafts/{draft_id}")
    assert draft_resp.status_code == 200
    orig_paths = draft_resp.json()["original_image_paths"]
    assert len(orig_paths) == 1
    
    # Load the saved file and verify its format is JPEG, not HEIC
    saved_path = orig_paths[0]
    assert os.path.exists(saved_path)
    
    img = Image.open(saved_path)
    assert img.format == "JPEG"
    
    # Clean up
    if os.path.exists(saved_path):
        os.remove(saved_path)

