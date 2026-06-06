import os
from database import (
    DATA_DIR, get_cached_file, add_cached_file,
    get_total_cache_size, get_oldest_cached_files, delete_cached_file
)
from services.drive_service import download_file_from_drive

CACHE_DIR = os.path.join(DATA_DIR, "cache")
# Cache size limit in Megabytes. Default is 500 MB.
CACHE_SIZE_LIMIT_MB = float(os.environ.get("CACHE_SIZE_LIMIT_MB", 500.0))

def get_image_file(drive_file_id: str) -> str:
    """
    Retrieves the local path of the image for a given drive_file_id.
    Downloads it from Google Drive and updates the LRU cache if necessary.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 1. Check if it's already in the cache database
    cached = get_cached_file(drive_file_id)
    if cached:
        # Check if the file actually exists on the filesystem
        if os.path.exists(cached["file_path"]):
            return cached["file_path"]
        else:
            # Database cache entry exists but file was deleted. Clean up.
            delete_cached_file(drive_file_id)

    # 2. Download from Google Drive
    dest_path = os.path.join(CACHE_DIR, f"{drive_file_id}.jpg")
    success = download_file_from_drive(drive_file_id, dest_path)
    if not success:
        raise IOError(f"Could not download file {drive_file_id} from Google Drive")

    # 3. Register in cache database
    file_size = os.path.getsize(dest_path)
    add_cached_file(drive_file_id, dest_path, file_size)

    # 4. Check size and evict oldest files if limit exceeded
    limit_bytes = int(CACHE_SIZE_LIMIT_MB * 1024 * 1024)
    while get_total_cache_size() > limit_bytes:
        # Evict in batches of 5 to minimize queries
        oldest_files = get_oldest_cached_files(limit=5)
        if not oldest_files:
            break
            
        for item in oldest_files:
            # Delete from disk
            if os.path.exists(item["file_path"]):
                try:
                    os.remove(item["file_path"])
                except Exception as e:
                    print(f"Error removing cached file {item['file_path']}: {e}")
            
            # Delete from database
            delete_cached_file(item["drive_file_id"])
            
            # Recheck size after each deletion to stop immediately if under limit
            if get_total_cache_size() <= limit_bytes:
                break

    return dest_path
