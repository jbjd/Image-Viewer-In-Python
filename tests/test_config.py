import os

import pytest

from image_viewer.config import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_FONT,
    DEFAULT_MAX_ITEMS_IN_CACHE,
    Config,
    DefaultKeybinds,
    _validate_hex_or_default,
    _validate_keybind_or_default,
)
from image_viewer.util._generic import is_valid_keybind
from tests.conftest import WORKING_DIR

_DEFAULT = "default"


def test_config_reader():
    """Should return all specified values"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config.ini")

    assert config.font_file == "test"
    assert config.max_items_in_cache == 999
    assert config.background_color == "#ABCDEF"

    assert config.keybinds.move_to_new_file == "<F6>"
    assert config.keybinds.show_details == "<Control-a>"
    assert config.keybinds.undo_most_recent_action == "<Control-Z>"


def test_config_reader_defaults():
    """Should return all default values"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config_empty.ini")

    assert config.font_file == DEFAULT_FONT
    assert config.max_items_in_cache == DEFAULT_MAX_ITEMS_IN_CACHE
    assert config.background_color == DEFAULT_BACKGROUND_COLOR

    assert (
        config.keybinds.copy_to_clipboard_as_base64
        == DefaultKeybinds.COPY_TO_CLIPBOARD_AS_BASE64
    )
    assert config.keybinds.move_to_new_file == DefaultKeybinds.MOVE_TO_NEW_FILE
    assert config.keybinds.refresh == DefaultKeybinds.REFRESH
    assert config.keybinds.reload_image == DefaultKeybinds.RELOAD_IMAGE
    assert config.keybinds.rename == DefaultKeybinds.RENAME
    assert config.keybinds.show_details == DefaultKeybinds.SHOW_DETAILS
    assert (
        config.keybinds.undo_most_recent_action
        == DefaultKeybinds.UNDO_MOST_RECENT_ACTION
    )


def test_config_reader_int_fallback():
    """Should return default when"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config_bad_values.ini")

    assert config.font_file == DEFAULT_FONT
    assert config.max_items_in_cache == DEFAULT_MAX_ITEMS_IN_CACHE
    assert config.background_color == DEFAULT_BACKGROUND_COLOR
    assert config.keybinds.move_to_new_file == DefaultKeybinds.MOVE_TO_NEW_FILE


@pytest.mark.parametrize(
    "keybind,expected_keybind",
    [
        ("asdvbiu34uiyg", _DEFAULT),
        ("<Control-d>", "<Control-d>"),
        ("<Control->", _DEFAULT),
        ("<F0>", _DEFAULT),
        ("<F1>", "<F1>"),
        ("<F12>", "<F12>"),
        ("<F13>", _DEFAULT),
        ("<F91>", _DEFAULT),
        ("<k>", _DEFAULT),
    ],
)
def test_validate_keybind_or_default(keybind: str, expected_keybind: str):
    """Should return original keybind or default if keybind was invalid"""
    assert _validate_keybind_or_default(keybind, _DEFAULT) == expected_keybind


def test_default_keybinds_are_valid():
    for keybind in DefaultKeybinds:
        assert is_valid_keybind(keybind)


@pytest.mark.parametrize(
    "hex_color,expected",
    [
        ("asdvbiu34uiyg", _DEFAULT),
        ("#010101", "#010101"),
        ("#01ABEF", "#01ABEF"),
        ("#01ABEG", _DEFAULT),
        ("#01", _DEFAULT),
    ],
)
def test_validate_hex_or_default(hex_color: str, expected: str):
    """Should return original hex or default if it was invalid"""
    assert _validate_hex_or_default(hex_color, _DEFAULT) == expected
