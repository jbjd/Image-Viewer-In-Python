"""A simple script to valid the config.ini file
to ensure it presents accurate examples"""

from configparser import ConfigParser

from schema import Schema

from image_viewer.util._generic import is_valid_hex_color, is_valid_keybind


def strip_quotes(value: str) -> str:
    """Values from .ini may be wrapped in quotes, return value without quotes"""
    return value.strip("'\"")


def empty_or_valid_hex_color(hex_color: str) -> bool:
    """Returns True if hex_color is in valid format '#abC123'"""
    hex_color = strip_quotes(hex_color)
    return hex_color == "" or is_valid_hex_color(hex_color)


def empty_or_valid_int(possible_int: str) -> bool:
    """Returns True if possible_int is an empty string or parsable as an int"""
    possible_int = strip_quotes(possible_int)
    try:
        return possible_int == "" or int(possible_int) >= 0
    except ValueError:
        return False


def empty_or_valid_keybind(keybind: str) -> bool:
    """Returns True if keybind is a valid subset of keybinds used for tkinter
    that this program accepts"""
    keybind = strip_quotes(keybind)
    return keybind == "" or is_valid_keybind(keybind)


schema = Schema(
    {
        "FONT": {"default": str},
        "CACHE": {"size": empty_or_valid_int},
        "KEYBINDS": {
            "copy_to_clipboard_as_base64": empty_or_valid_keybind,
            "move_to_new_file": empty_or_valid_keybind,
            "refresh": empty_or_valid_keybind,
            "reload_image": empty_or_valid_keybind,
            "rename": empty_or_valid_keybind,
            "show_details": empty_or_valid_keybind,
            "undo_most_recent_action": empty_or_valid_keybind,
            "zoom_in": empty_or_valid_keybind,
            "zoom_out": empty_or_valid_keybind,
        },
        "UI": {"background_color": empty_or_valid_hex_color},
    }
)


config_parser = ConfigParser()
config_parser.read("image_viewer/config.ini")

config: dict = {}
for section in config_parser.sections():
    config[section] = {}
    for option in config_parser.options(section):
        config[section][option] = config_parser.get(section, option)

schema.validate(config)
