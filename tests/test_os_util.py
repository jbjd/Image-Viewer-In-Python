import os
from unittest.mock import patch

import pytest

from image_viewer.util.os import (
    clean_str_for_OS_path,
    get_byte_display,
    kb_size,
    maybe_truncate_long_name,
    split_name_and_suffix,
    walk_dir,
)
from tests.conftest import IMG_DIR


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


@pytest.mark.parametrize(
    "name,expected_name",
    [
        ("short.png", "short.png"),
        ("0123456789" * 10 + ".png", "0123456789" * 4 + "(…).png"),
    ],
)
def test_truncate_long_name(name: str, expected_name: str):
    """Should truncate names longer than 40 characters"""
    assert maybe_truncate_long_name(name) == expected_name


@pytest.mark.parametrize(
    "name_and_suffix,expected_name,expected_suffix",
    [
        ("test.png", "test", ".png"),
        ("test", "test", ""),
    ],
)
def test_split_name_and_suffix(
    name_and_suffix: str, expected_name: str, expected_suffix: str
):
    name, suffix = split_name_and_suffix(name_and_suffix)

    assert name == expected_name
    assert suffix == expected_suffix


def test_walk_dir():
    """Test that walk_dir correctly finds files in dir"""
    files = [p for p in walk_dir(IMG_DIR)]
    assert len(files) == 5

    # When is_dir raises os error, assume not a dir like os module does
    with patch.object(os.DirEntry, "is_dir", side_effect=OSError):
        files = [p for p in walk_dir(IMG_DIR)]
        assert len(files) == 5
