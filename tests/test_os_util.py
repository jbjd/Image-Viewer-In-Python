import os
from unittest.mock import patch

import pytest

from image_viewer.util.os import (
    clean_str_for_OS_path,
    get_byte_display,
    maybe_truncate_long_name,
    split_name_and_suffix,
    walk_dir,
)
from tests.conftest import IMG_DIR


@pytest.mark.parametrize(
    "os_name,expected_path",
    [
        # Any OS other than Windows no-ops
        ("nt", "StringWithIllegalCharacters.png"),
        ("linux", 'String:"|*With?Illegal<Characters>.png'),
    ],
)
def test_clean_str_for_OS_path(os_name: str, expected_path: str):
    """Test that illegal characters for given OS are removed from string"""
    problematic_path: str = 'String:"|*With?Illegal<Characters>.png'

    with patch.object(os, "name", os_name):
        cleaned_path: str = clean_str_for_OS_path(problematic_path)
        assert cleaned_path == expected_path


@pytest.mark.parametrize("os_name", ["nt", "linux"])
def test_get_byte_display(os_name: str):
    """Should take bytes and return correct string representing kb/mb on given OS"""
    kb_size: int = 1024 if os_name == "nt" else 1000
    expected_display_999kb: str = "999kb"
    expected_display_1000kb: str = "0.98mb" if os_name == "nt" else "1.00mb"

    with patch.object(os, "name", os_name):
        assert get_byte_display(999 * kb_size) == expected_display_999kb
        assert get_byte_display(1000 * kb_size) == expected_display_1000kb


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
    [("test.png", "test", ".png"), ("test", "test", "")],
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
