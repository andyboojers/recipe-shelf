import os
import pytest
from services.drive_service import get_drive_service, CREDENTIALS_FILE, upload_file_to_drive, download_file_from_drive
from googleapiclient.errors import HttpError

# Automatically skip all tests in this file if token.json is not present locally
pytestmark = pytest.mark.skipif(
    not os.path.exists(CREDENTIALS_FILE),
    reason=f"Integration test skipped because Google Drive token was not found at {CREDENTIALS_FILE}"
)

def test_drive_integration_upload_and_download():
    """
    Integration test that connects to the actual Google Drive API to:
    1. Upload a temporary text file.
    2. Download it back.
    3. Verify the file contents match exactly.
    4. Clean up the file from Google Drive and local disk.
    """
    service = get_drive_service()
    assert service is not None, "Failed to get active Google Drive service"
    
    # 1. Create a temporary local file
    temp_local_file = "temp_integration_test.txt"
    with open(temp_local_file, "w") as f:
        f.write("Integration test content: hello world!")
        
    uploaded_file_id = None
    downloaded_local_file = "temp_integration_downloaded.txt"
    
    try:
        # 2. Upload file to Google Drive root folder
        uploaded_file_id = upload_file_to_drive(
            service=service,
            file_path=temp_local_file,
            name="integration_test_file.txt",
            mime_type="text/plain",
            parent_id="root"
        )
        assert uploaded_file_id is not None
        
        # 3. Download the file back using our download function
        success = download_file_from_drive(uploaded_file_id, downloaded_local_file)
        assert success is True
        
        # 4. Verify downloaded file content matches original
        with open(downloaded_local_file, "r") as f:
            content = f.read()
        assert content == "Integration test content: hello world!"
        
    finally:
        # Clean up local temporary files
        if os.path.exists(temp_local_file):
            os.remove(temp_local_file)
        if os.path.exists(downloaded_local_file):
            os.remove(downloaded_local_file)
            
        # 5. Clean up remote file on Google Drive
        if uploaded_file_id:
            try:
                service.files().delete(fileId=uploaded_file_id).execute()
            except HttpError as e:
                print(f"Warning: Failed to delete remote test file from Google Drive: {e}")
