import pytest
from services.drive_service import extract_folder_id

def test_extract_folder_id_raw():
    raw_id = "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"
    assert extract_folder_id(raw_id) == raw_id

def test_extract_folder_id_standard_url():
    url = "https://drive.google.com/drive/folders/1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"
    assert extract_folder_id(url) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_extract_folder_id_user_routing_url():
    url = "https://drive.google.com/drive/u/0/folders/1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"
    assert extract_folder_id(url) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_extract_folder_id_url_with_query_params():
    url = "https://drive.google.com/drive/u/0/folders/1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V?usp=sharing"
    assert extract_folder_id(url) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_extract_folder_id_open_url():
    url = "https://drive.google.com/open?id=1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"
    assert extract_folder_id(url) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_extract_folder_id_open_url_with_other_params():
    url = "https://drive.google.com/open?usp=sharing&id=1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"
    assert extract_folder_id(url) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_extract_folder_id_empty_or_none():
    assert extract_folder_id(None) is None
    assert extract_folder_id("") == ""

def test_extract_folder_id_spaces():
    raw_id_with_spaces = "  1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V   "
    assert extract_folder_id(raw_id_with_spaces) == "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V"

def test_create_recipe_folder_404_error(monkeypatch):
    from unittest.mock import MagicMock
    from googleapiclient.errors import HttpError
    from services.drive_service import create_recipe_folder
    import httplib2

    # Mock RECIPE_ROOT_FOLDER_ID
    monkeypatch.setattr("services.drive_service.RECIPE_ROOT_FOLDER_ID", "1pD_o_G-KL6ie_lRNu7a4fs4EcxecSq-V")

    # Mock googleapiclient service
    mock_service = MagicMock()
    
    # Create an HttpError mock response
    resp = httplib2.Response({"status": 404})
    content = b"File not found"
    http_error = HttpError(resp, content)
    
    # Set the create().execute() chain to raise the error
    mock_service.files.return_value.create.return_value.execute.side_effect = http_error
    
    with pytest.raises(RuntimeError) as exc_info:
        create_recipe_folder(mock_service, "test-folder")
        
    assert "not found or not accessible" in str(exc_info.value)
    assert "grant it 'Editor' access" in str(exc_info.value)
