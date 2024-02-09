import pytest
import os

from image_viewer.util.os import clean_str_for_OS_path, walk_dir


@pytest.mark.skipif(os.name != "nt", reason="Only relevant to Windows")
def test_clean_str_for_OS_path():
    """Test that illegal characters for OS are removed from string"""
    bad_name: str = 'String:"|*With?Illegal<Characters>.png'
    good_name: str = clean_str_for_OS_path(bad_name)
    assert good_name == "StringWithIllegalCharacters.png"


def test_walk_dir(img_dir: str):
    """Test that walk_dir behaves like expected"""
    files = [p for p in walk_dir(img_dir)]
    assert len(files) == 5
