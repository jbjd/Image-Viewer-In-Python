import pytest

from image_viewer.config.validate import validate_or_default


DEFAULT = "default"


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
