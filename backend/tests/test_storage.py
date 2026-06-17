import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, save_draft, save_recipe_cache, get_db, DATA_DIR
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
    save_draft(draft_id, "Draft Recipe", ["Flour"], ["Mix"], "Notes", "4", "30 mins", ["test"], "path/to/img.jpg")
    
    response = client.get(f"/api/drafts/{draft_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Draft Recipe"

def test_post_recipes_endpoint(mocker):
    draft_id = str(uuid.uuid4())
    save_draft(draft_id, "To Be Saved", [], [], "", "4", "30 mins", [], "")
    
    # Mock the drive service to avoid real uploads
    mocker.patch("main.save_recipe_to_drive", return_value=("drive_file_id_123", "image_drive_id_123", "original_drive_id_123"))
    
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
    save_recipe_cache(recipe_id, "Unique Pancake", ["Flour", "Milk"], ["Cook"], "Delicious", "4", "30 mins", ["breakfast"], "file1", "img1")
    
    response = client.get("/api/recipes?q=Pancake")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Unique Pancake"

def test_get_recipe_endpoint():
    recipe_id = str(uuid.uuid4())
    save_recipe_cache(recipe_id, "Specific Recipe", [], [], "", "4", "30 mins", [], "file1", "img1")
    
    response = client.get(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Recipe"

def test_get_draft_image_endpoint():
    draft_id = str(uuid.uuid4())
    import os
    
    drafts_dir = os.path.join(DATA_DIR, "drafts")
    os.makedirs(drafts_dir, exist_ok=True)
    img_path = os.path.join(drafts_dir, f"{draft_id}.jpg")
    
    with open(img_path, "wb") as f:
        f.write(b"fake_image_content")
        
    save_draft(draft_id, "Draft With Image", [], [], "", "", "", [], img_path)
    
    response = client.get(f"/api/drafts/{draft_id}/image")
    assert response.status_code == 200
    assert response.content == b"fake_image_content"
    
    if os.path.exists(img_path):
        os.remove(img_path)

def test_delete_recipe_endpoint(mocker):
    recipe_id = str(uuid.uuid4())
    save_recipe_cache(recipe_id, "Recipe to Delete", [], [], "", "4", "30 mins", [], "file_to_delete", "img_to_delete")
    
    mocker.patch("main.delete_recipe_folder", return_value=None)
    
    response = client.delete(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Check that recipe is deleted
    get_resp = client.get(f"/api/recipes/{recipe_id}")
    assert get_resp.status_code == 404
