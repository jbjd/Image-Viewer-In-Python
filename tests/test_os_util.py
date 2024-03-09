import os
from unittest.mock import patch

import pytest

from image_viewer.util.os import (
    clean_str_for_OS_path,
    get_byte_display,
    kb_size,
    truncate_path,
    walk_dir,
)


@pytest.mark.skipif(os.name != "nt", reason="Only relevant to Windows")
def test_clean_str_for_OS_path():
    """Test that illegal characters for OS are removed from string"""
    bad_name: str = 'String:"|*With?Illegal<Characters>.png'
    good_name: str = clean_str_for_OS_path(bad_name)
    assert good_name == "StringWithIllegalCharacters.png"


@pytest.mark.skipif(os.name != "nt", reason="Uses Windows definition of kb/mb")
def test_get_byte_display_nt():
    """Should take bytes and return correct string representing kb/mb"""
    assert get_byte_display(999 * kb_size) == "999kb"
    assert get_byte_display(1000 * kb_size) == "0.98mb"


@pytest.mark.skipif(os.name == "nt", reason="Non-Windows definition of kb/mb")
def test_get_byte_display_linux():
    """Should take bytes and return correct string representing kb/mb"""
    assert get_byte_display(999 * kb_size) == "999kb"
    assert get_byte_display(1000 * kb_size) == "1.00mb"


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


def test_walk_dir(img_dir: str):
    """Test that walk_dir correctly finds files in dir"""
    files = [p for p in walk_dir(img_dir)]
    assert len(files) == 5

    # When is_dir raises os error, assume not a dir like os module does
    with patch.object(os.DirEntry, "is_dir", side_effect=OSError):
        files = [p for p in walk_dir(img_dir)]
        assert len(files) == 5
