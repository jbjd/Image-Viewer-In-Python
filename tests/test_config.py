import os

import pytest

from image_viewer.config import (
    Config,
    validate_hex_or_default,
    validate_keybind_or_default,
)
from image_viewer.constants import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_FONT,
    DEFAULT_MAX_ITEMS_IN_CACHE,
)
from tests.conftest import WORKING_DIR

DEFAULT = "default"


def test_config_reader():
    """Should return all default values"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config.ini")

    assert config.font_file == "test"
    assert config.max_items_in_cache == 999
    assert config.background_color == "#ABCDEF"


def test_config_reader_defaults():
    """Should return all default values"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config_empty.ini")

    assert config.font_file == DEFAULT_FONT
    assert config.max_items_in_cache == DEFAULT_MAX_ITEMS_IN_CACHE
    assert config.background_color == DEFAULT_BACKGROUND_COLOR


def test_config_reader_int_fallback():
    """Should return default when"""
    config = Config(os.path.join(WORKING_DIR, "data"), "config_bad_values.ini")

    assert config.font_file == DEFAULT_FONT
    assert config.max_items_in_cache == DEFAULT_MAX_ITEMS_IN_CACHE
    assert config.background_color == DEFAULT_BACKGROUND_COLOR


@pytest.mark.parametrize(
    "keybind,expected_keybind",
    [
        ("asdvbiu34uiyg", DEFAULT),
        ("<Control-d>", "<Control-d>"),
        ("<Control->", DEFAULT),
        ("<F0>", DEFAULT),
        ("<F1>", "<F1>"),
        ("<F12>", "<F12>"),
        ("<F13>", DEFAULT),
        ("<F91>", DEFAULT),
    ],
)
def test_validate_keybind_or_default(keybind: str, expected_keybind: str):
    """Should return original keybind or default if keybind was invalid"""
    assert validate_keybind_or_default(keybind, DEFAULT) == expected_keybind


@pytest.mark.parametrize(
    "hex,expected_hex",
    [
        ("asdvbiu34uiyg", DEFAULT),
        ("#010101", "#010101"),
        ("#01ABEF", "#01ABEF"),
        ("#01ABEG", DEFAULT),
        ("#01", DEFAULT),
    ],
)
def test_validate_hex_or_default(hex: str, expected_hex: str):
    """Should return original hex or default if it was invalid"""
    assert validate_hex_or_default(hex, DEFAULT) == expected_hex
