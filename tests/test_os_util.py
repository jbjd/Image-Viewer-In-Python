import os

import pytest

from image_viewer.util.os import clean_str_for_OS_path, walk_dir, truncate_path


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


def test_truncate_path():
    # test truncating . to same directory
    assert truncate_path("/./asdf") == "/asdf"
    assert truncate_path("asdf/./123/.") == "asdf/123/"

    # test truncating .. to previous directory
    assert truncate_path("abc/123/..") == "abc/"
    assert truncate_path("abc/123/../") == "abc/"
    assert truncate_path("abc/./123/../.") == "abc/"


@pytest.mark.skipif(os.name != "nt", reason="Only relevant to Windows")
def test_truncate_path_nt():
    assert truncate_path("C:/.\\asdf\\.\\") == "C:/asdf/"
    assert truncate_path("C:/abc\\./123/..\\.") == "C:/abc/"
