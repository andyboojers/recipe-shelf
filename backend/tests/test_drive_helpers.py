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
