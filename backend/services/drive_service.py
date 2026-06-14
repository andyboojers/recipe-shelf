import os
import json
import re
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io

DATA_DIR = os.environ.get("DATA_DIR", "./data")
CREDENTIALS_FILE = os.path.join(DATA_DIR, "secrets/token.json")
SERVICE_ACCOUNT_FILE = os.environ.get("SERVICE_ACCOUNT_FILE", os.path.join(DATA_DIR, "secrets/service_account.json"))

def extract_folder_id(folder_input: str) -> str:
    if not folder_input:
        return folder_input
    folder_input = folder_input.strip()
    if folder_input.startswith(("http://", "https://")):
        # e.g., https://drive.google.com/drive/folders/1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V
        # or https://drive.google.com/drive/u/0/folders/1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V
        match = re.search(r'folders/([a-zA-Z0-9-_]+)', folder_input)
        if match:
            return match.group(1)
        # e.g., https://drive.google.com/open?id=1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V
        match = re.search(r'[?&]id=([a-zA-Z0-9-_]+)', folder_input)
        if match:
            return match.group(1)
    return folder_input

RECIPE_ROOT_FOLDER_ID = extract_folder_id(os.environ.get("RECIPE_ROOT_FOLDER_ID"))

def get_drive_service():
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, ["https://www.googleapis.com/auth/drive.file"])
        return build("drive", "v3", credentials=creds)
    
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    
    use_mock = os.environ.get("USE_MOCK_DRIVE", "false").lower() == "true"
    if use_mock:
        print(f"Warning: No Google Drive credentials found. Using mock mode.")
        return None
        
    raise RuntimeError("Google Drive credentials (token.json or service_account.json) not found and USE_MOCK_DRIVE is not true. Drive sync cannot proceed.")

def create_recipe_folder(service, folder_name):
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [RECIPE_ROOT_FOLDER_ID] if RECIPE_ROOT_FOLDER_ID else []
    }
    try:
        folder = service.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")
    except HttpError as e:
        if e.resp.status == 404 and RECIPE_ROOT_FOLDER_ID:
            raise RuntimeError(
                f"Google Drive folder '{RECIPE_ROOT_FOLDER_ID}' not found or not accessible. "
                "If you are using a Service Account, make sure to share the Google Drive folder "
                "with the service account email address (found in your service account JSON file under 'client_email') "
                "and grant it 'Editor' access."
            ) from e
        raise e

def upload_file_to_drive(service, file_path, name, mime_type, parent_id):
    file_metadata = {
        "name": name,
        "parents": [parent_id]
    }
    media = MediaFileUpload(file_path, mimetype=mime_type)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")

def save_recipe_to_drive(recipe_id: str, recipe_data: dict, image_path: str, original_image_path: str = None):
    """
    Saves a recipe to Google Drive:
    1. Creates a folder named after recipe_id
    2. Uploads the recipe.json
    3. Uploads the original scan image
    4. Uploads the cropped thumbnail image (if exists)
    """
    service = get_drive_service()
    if not service:
        # Mocking for local dev if tokens aren't set
        print(f"Mocking Drive save for {recipe_id}")
        mock_img = f"local:{image_path}" if image_path else "mock_image_drive_id"
        mock_orig = f"local:{original_image_path}" if original_image_path else "mock_original_drive_id"
        return "mock_drive_file_id", mock_img, mock_orig

    # Create folder
    folder_id = create_recipe_folder(service, recipe_id)

    # Save JSON locally first
    json_path = os.path.join(DATA_DIR, f"drafts/{recipe_id}_recipe.json")
    with open(json_path, "w") as f:
        json.dump(recipe_data, f, indent=2)

    # Upload JSON
    drive_file_id = upload_file_to_drive(service, json_path, "recipe.json", "application/json", folder_id)

    # Upload Original Image
    original_drive_id = None
    if original_image_path and os.path.exists(original_image_path):
        original_drive_id = upload_file_to_drive(service, original_image_path, "original.jpg", "image/jpeg", folder_id)

    # Upload Cropped Thumbnail Image
    image_drive_id = None
    if image_path and os.path.exists(image_path):
        image_drive_id = upload_file_to_drive(service, image_path, "thumbnail.jpg", "image/jpeg", folder_id)

    return drive_file_id, image_drive_id, original_drive_id

def download_file_from_drive(drive_file_id: str, dest_path: str) -> bool:
    """
    Downloads a file from Google Drive and saves it to dest_path.
    Returns True if successful, False otherwise.
    """
    service = get_drive_service()
    if not service:
        # If mock mode is active, we write dummy data for testing / local development
        print(f"Mocking Drive download for {drive_file_id}")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        if drive_file_id.startswith("local:"):
            import shutil
            src_path = drive_file_id[6:]
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_path)
                return True
        with open(dest_path, "wb") as f:
            f.write(b"dummy_mocked_image_from_drive")
        return True

    try:
        request = service.files().get_media(fileId=drive_file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(file_stream.getvalue())
        return True
    except Exception as e:
        print(f"Failed to download file {drive_file_id} from Drive: {e}")
        return False
