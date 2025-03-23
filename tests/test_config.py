import os

import pytest

from image_viewer.config import Config, validate_or_default
from image_viewer.constants import DEFAULT_FONT, DEFAULT_MAX_ITEMS_IN_CACHE
from tests.conftest import WORKING_DIR

DEFAULT = "default"


def test_config_reader():
    config = Config(os.path.join(WORKING_DIR, "data/empty_config.ini"))

    assert config.font_file == DEFAULT_FONT
    assert config.max_items_in_cache == DEFAULT_MAX_ITEMS_IN_CACHE


@pytest.mark.parametrize(
    "keybind,expected_result",
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
def test_validate_or_default(keybind: str, expected_result: str):
    """should return original keybind or default if keybind was invalid"""
    assert validate_or_default(keybind, DEFAULT) == expected_result
