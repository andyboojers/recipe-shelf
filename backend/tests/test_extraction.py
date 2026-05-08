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
    mocker.patch("main.extract_recipes_from_images", return_value=[{
        "title": "Mocked Recipe 1",
        "ingredients": ["Mock ingredient"],
        "instructions": ["Mock instruction"],
        "notes": "Mock note",
        "page_index": 0,
        "image_bounding_box": {"ymin": 0.1, "xmin": 0.1, "ymax": 0.9, "xmax": 0.9}
    }])
    
    response = client.post(
        "/api/extract",
        json={"image_data": "base64_encoded_dummy_string"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["draft_ids"]) == 1
    draft_id = data["draft_ids"][0]
    
    # Verify draft was created
    draft_resp = client.get(f"/api/drafts/{draft_id}")
    assert draft_resp.status_code == 200
    assert draft_resp.json()["title"] == "Mocked Recipe 1"
