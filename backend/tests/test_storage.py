import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, save_draft, save_recipe_cache, get_db
import uuid

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    # Clean up before tests
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM drafts")
    cursor.execute("DELETE FROM recipes_cache")
    cursor.execute("DELETE FROM recipe_search")
    conn.commit()
    conn.close()

def test_get_draft_endpoint():
    draft_id = str(uuid.uuid4())
    save_draft(draft_id, "Draft Recipe", ["Flour"], ["Mix"], "Notes", "path/to/img.jpg")
    
    response = client.get(f"/api/drafts/{draft_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Draft Recipe"

def test_post_recipes_endpoint(mocker):
    draft_id = str(uuid.uuid4())
    save_draft(draft_id, "To Be Saved", [], [], "", "")
    
    # Mock the drive service to avoid real uploads
    mocker.patch("main.save_recipe_to_drive", return_value=("drive_file_id_123", "image_drive_id_123"))
    
    payload = {
        "draft_id": draft_id,
        "title": "Saved Recipe",
        "ingredients": ["Egg"],
        "instructions": ["Fry"],
        "notes": "Good"
    }
    response = client.post("/api/recipes", json=payload)
    assert response.status_code == 200
    
    # Check that draft is deleted
    draft_resp = client.get(f"/api/drafts/{draft_id}")
    assert draft_resp.status_code == 404

def test_search_recipes_endpoint():
    recipe_id = str(uuid.uuid4())
    save_recipe_cache(recipe_id, "Unique Pancake", ["Flour", "Milk"], ["Cook"], "Delicious", "file1", "img1")
    
    response = client.get("/api/recipes?q=Pancake")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Unique Pancake"

def test_get_recipe_endpoint():
    recipe_id = str(uuid.uuid4())
    save_recipe_cache(recipe_id, "Specific Recipe", [], [], "", "file1", "img1")
    
    response = client.get(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Recipe"
