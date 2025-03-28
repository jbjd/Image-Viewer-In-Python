import os
from unittest.mock import patch

import pytest

from image_viewer.util.os import (
    get_byte_display,
    maybe_truncate_long_name,
    open_with,
    split_name_and_suffix,
    show_info_popup,
    walk_dir,
)
from tests.conftest import IMG_DIR
from tests.test_util.mocks import MockWindll


@pytest.mark.parametrize("os_name", ["nt", "linux"])
def test_get_byte_display(os_name: str):
    """Should take bytes and return correct string representing kb/mb on given OS"""
    kb_size: int = 1024 if os_name == "nt" else 1000
    expected_display_999kb: str = "999kb"
    expected_display_1000kb: str = "0.98mb" if os_name == "nt" else "1.00mb"

    with patch.object(os, "name", os_name):
        assert get_byte_display(999 * kb_size) == expected_display_999kb
        assert get_byte_display(1000 * kb_size) == expected_display_1000kb


@pytest.mark.parametrize("os_name", ["nt", "linux"])
def test_open_with(os_name: str):
    """Should call windows API with correct params"""
    hwnd = 1
    path = "test"

    with patch.object(os, "name", os_name):
        if os_name != "nt":
            with pytest.raises(NotImplementedError):
                open_with(hwnd, path)
        else:
            EXECUTE_JUST_ONCE_FLAGS = 0x24
            mock_windll = MockWindll()

            with patch("image_viewer.util.os.windll", create=True, new=mock_windll):
                open_with(hwnd, path)

            mock_windll.shell32.SHOpenWithDialog.assert_called_once()

            call_args = mock_windll.shell32.SHOpenWithDialog.call_args[0]
            assert call_args[0] == hwnd
            assert getattr(call_args[1], "pcszFile", None) == path
            assert getattr(call_args[1], "oaifInFlags", None) == EXECUTE_JUST_ONCE_FLAGS


@pytest.mark.parametrize("os_name", ["nt", "linux"])
def test_show_info_popup(os_name: str):
    """Should call different popups depending on OS"""
    hwnd = 123
    title = "title"
    body = "body"

    with patch.object(os, "name", os_name):
        if os_name == "nt":
            mock_windll = MockWindll()
            expected_flags = 0

            with patch("image_viewer.util.os.windll", create=True, new=mock_windll):
                show_info_popup(hwnd, title, body)

            mock_windll.user32.MessageBoxW.assert_called_once_with(
                hwnd, body, title, expected_flags
            )
        else:
            with patch("image_viewer.util.os.showinfo", create=True) as mock_showinfo:
                show_info_popup(hwnd, title, body)

                mock_showinfo.assert_called_once_with(title, body)


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
