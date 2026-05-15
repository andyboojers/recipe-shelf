import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DATA_DIR = os.environ.get("DATA_DIR", "./data")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "secrets/token.json")
RECIPE_ROOT_FOLDER_ID = os.environ.get("RECIPE_ROOT_FOLDER_ID")

def get_drive_service():
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, ["https://www.googleapis.com/auth/drive.file"])
        return build("drive", "v3", credentials=creds)
    
    use_mock = os.environ.get("USE_MOCK_DRIVE", "false").lower() == "true"
    if use_mock:
        print(f"Warning: Google Drive token.json not found at {CREDENTIALS_FILE}. Using mock mode.")
        return None
        
    raise RuntimeError(f"Google Drive token.json not found at {CREDENTIALS_FILE} and USE_MOCK_DRIVE is not true. Drive sync cannot proceed.")

def create_recipe_folder(service, folder_name):
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [RECIPE_ROOT_FOLDER_ID] if RECIPE_ROOT_FOLDER_ID else []
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

def upload_file_to_drive(service, file_path, name, mime_type, parent_id):
    file_metadata = {
        "name": name,
        "parents": [parent_id]
    }
    media = MediaFileUpload(file_path, mimetype=mime_type)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")

def save_recipe_to_drive(recipe_id: str, recipe_data: dict, image_path: str):
    """
    Saves a recipe to Google Drive:
    1. Creates a folder named after recipe_id
    2. Uploads the recipe.json
    3. Uploads the image (if exists)
    """
    service = get_drive_service()
    if not service:
        # Mocking for local dev if tokens aren't set
        print(f"Mocking Drive save for {recipe_id}")
        return "mock_drive_file_id", "mock_image_drive_id"

    # Create folder
    folder_id = create_recipe_folder(service, recipe_id)

    # Save JSON locally first
    json_path = os.path.join(DATA_DIR, f"drafts/{recipe_id}_recipe.json")
    with open(json_path, "w") as f:
        json.dump(recipe_data, f, indent=2)

    # Upload JSON
    drive_file_id = upload_file_to_drive(service, json_path, "recipe.json", "application/json", folder_id)

    # Upload Image
    image_drive_id = None
    if image_path and os.path.exists(image_path):
        image_drive_id = upload_file_to_drive(service, image_path, "original.jpg", "image/jpeg", folder_id)

    return drive_file_id, image_drive_id
