import pytest
from services.drive_service import extract_folder_id, generate_human_readable_folder_name

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

def test_generate_human_readable_folder_name():
    recipe_id = "d3b07384-d113-4683-bf28-df8b100afcf5"
    
    # 1. Clean alphanumeric
    assert generate_human_readable_folder_name("Spaghetti Carbonara", recipe_id) == "spaghetti_carbonara_d3b07384"
    
    # 2. Punctuation and special characters
    assert generate_human_readable_folder_name("Grandma's Apple Pie!", recipe_id) == "grandmas_apple_pie_d3b07384"
    
    # 3. Truncation to 60 characters
    long_title = "a" * 80
    assert generate_human_readable_folder_name(long_title, recipe_id) == "a" * 60 + "_d3b07384"
    
    # 4. Truncation with trailing underscores
    long_title_with_spaces = "a " * 40
    res = generate_human_readable_folder_name(long_title_with_spaces, recipe_id)
    base_name = res[:-9] # strip the _d3b07384 (9 chars)
    assert len(base_name) <= 60
    assert not base_name.endswith("_")
    
    # 5. Empty or purely symbolic title
    assert generate_human_readable_folder_name("!!!", recipe_id) == "recipe_d3b07384"
    assert generate_human_readable_folder_name("", recipe_id) == "recipe_d3b07384"
    assert generate_human_readable_folder_name(None, recipe_id) == "recipe_d3b07384"

def test_generate_human_readable_folder_name_empty_uuid():
    # Test fallback when recipe_id is empty
    assert generate_human_readable_folder_name("Pasta", "") == "pasta"
    assert generate_human_readable_folder_name("Pasta", None) == "pasta"

