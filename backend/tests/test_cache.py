import pytest
import os
import shutil
import tempfile
from fastapi.testclient import TestClient
from main import app
from database import (
    init_db, get_db, DATA_DIR,
    get_cached_file, add_cached_file, get_total_cache_size,
    get_oldest_cached_files, delete_cached_file
)
from services.cache_service import get_image_file, CACHE_DIR

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    # Clean up DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM file_cache")
    conn.commit()
    conn.close()
    
    # Ensure cache dir exists and is empty for tests
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)
    yield
    # Clean up cache dir after tests
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)

def test_database_cache_crud():
    # 1. Add file to cache
    add_cached_file("file_id_123", "/fake/path/1.jpg", 1000)
    
    # 2. Get total size
    assert get_total_cache_size() == 1000
    
    # 3. Get cached file and verify last_accessed updates
    cached = get_cached_file("file_id_123")
    assert cached is not None
    assert cached["file_path"] == "/fake/path/1.jpg"
    assert cached["file_size"] == 1000
    
    # 4. Get non-existent
    assert get_cached_file("invalid_id") is None

def test_lru_eviction_retrieval():
    add_cached_file("file_1", "/fake/path/1.jpg", 100)
    add_cached_file("file_2", "/fake/path/2.jpg", 200)
    add_cached_file("file_3", "/fake/path/3.jpg", 300)
    
    # Access file_1 to make it "recently used"
    get_cached_file("file_1")
    
    # The oldest should be file_2, then file_3
    oldest = get_oldest_cached_files(limit=2)
    assert len(oldest) == 2
    assert oldest[0]["drive_file_id"] == "file_2"
    assert oldest[1]["drive_file_id"] == "file_3"

def test_cache_service_fetches_and_evicts(mocker):
    # Mock download_file_from_drive to just write a fake file
    def mock_download(drive_file_id, dest_path):
        with open(dest_path, "wb") as f:
            f.write(b"a" * 1024) # 1KB file
        return True
        
    mocker.patch("services.cache_service.download_file_from_drive", side_effect=mock_download)
    
    # Override the CACHE_SIZE_LIMIT_MB for testing (e.g. set to 2KB limit)
    mocker.patch("services.cache_service.CACHE_SIZE_LIMIT_MB", 0.002) # 2 KB = 2048 bytes
    
    # Fetch file 1 (1KB)
    path1 = get_image_file("drive_1")
    assert os.path.exists(path1)
    assert get_total_cache_size() == 1024
    
    # Fetch file 2 (1KB)
    path2 = get_image_file("drive_2")
    assert os.path.exists(path2)
    assert get_total_cache_size() == 2048
    
    # Fetch file 3 (1KB) -> this triggers eviction because total size would be 3072 (> 2048 limit)
    # Since drive_1 was fetched first, it should be the oldest and thus evicted
    path3 = get_image_file("drive_3")
    assert os.path.exists(path3)
    assert get_total_cache_size() <= 2048
    
    # Verify drive_1 is deleted from disk and database
    assert not os.path.exists(path1)
    assert get_cached_file("drive_1") is None
    
    # Verify drive_2 and drive_3 still exist
    assert os.path.exists(path2)
    assert os.path.exists(path3)

def test_api_endpoint_serves_image(mocker):
    # Mock cache service to return a dummy file we create
    dummy_path = os.path.join(CACHE_DIR, "test_api.jpg")
    with open(dummy_path, "wb") as f:
        f.write(b"api_image_data")
        
    mocker.patch("main.get_image_file", return_value=dummy_path)
    
    response = client.get("/api/files/some_drive_id")
    assert response.status_code == 200
    assert response.content == b"api_image_data"
