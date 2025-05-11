"""
Reads config.ini from root directory and stores results or defaults
"""

import os
import re
from configparser import ConfigParser

from constants import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_FONT,
    DEFAULT_MAX_ITEMS_IN_CACHE,
    DefaultKeybinds,
)


class Config:
    """Reads configs from config.ini"""

    __slots__ = ("background_color", "font_file", "keybinds", "max_items_in_cache")

    def __init__(
        self, working_directory: str, config_file_name: str = "config.ini"
    ) -> None:
        config_parser: ConfigParserExt = ConfigParserExt()
        config_parser.read(os.path.join(working_directory, config_file_name))

        self.font_file: str = config_parser.get_string_safe(
            "FONT", "DEFAULT", DEFAULT_FONT
        )
        self.max_items_in_cache: int = config_parser.get_int_safe(
            "CACHE", "SIZE", DEFAULT_MAX_ITEMS_IN_CACHE
        )

        self.keybinds = KeybindConfig(
            config_parser.get_string_safe("KEYBINDS", "MOVE_TO_NEW_FILE"),
            config_parser.get_string_safe("KEYBINDS", "SHOW_DETAILS"),
            config_parser.get_string_safe("KEYBINDS", "UNDO_MOST_RECENT_ACTION"),
        )

        self.background_color = validate_hex_or_default(
            config_parser.get_string_safe(
                "UI", "BACKGROUND_COLOR", DEFAULT_BACKGROUND_COLOR
            ),
            DEFAULT_BACKGROUND_COLOR,
        )


class KeybindConfig:
    """Contains configurable tkinter keybinds"""

    __slots__ = ("move_to_new_file", "show_details", "undo_most_recent_action")

    def __init__(
        self, move_to_new_file: str, show_details: str, undo_most_recent_action: str
    ) -> None:
        self.move_to_new_file: str = validate_keybind_or_default(
            move_to_new_file, DefaultKeybinds.MOVE_TO_NEW_FILE
        )
        self.show_details: str = validate_keybind_or_default(
            show_details, DefaultKeybinds.SHOW_DETAILS
        )
        self.undo_most_recent_action: str = validate_keybind_or_default(
            undo_most_recent_action, DefaultKeybinds.UNDO_MOST_RECENT_ACTION
        )


def validate_keybind_or_default(keybind: str, default: str) -> str:
    """Given a tkinter keybind, validate if its allowed
    and return keybind if its valid or the default if its not"""
    f_key_re = r"F([1-9]|10|11|12)"
    control_key_re = r"Control-[a-zA-Z0-9]"

    match = re.match(f"^<(({f_key_re})|({control_key_re}))>$", keybind)

    return default if match is None else keybind


def validate_hex_or_default(hex_code: str, default: str) -> str:
    """Returns hex_code if its in the valid hex format or default if not"""
    if len(hex_code) == 7 and all(
        c in "0123456789abcdefABCDEF" if index > 0 else c == "#"
        for index, c in enumerate(hex_code)
    ):
        return hex_code

    return default


class ConfigParserExt(ConfigParser):
    """Extends ConfigParser to add safer implementations of get"""

    def get_int_safe(self, section: str, option: str, fallback: int) -> int:
        """Returns config option converted to int or default if convert fails"""
        try:
            result: int = int(super().get(section, option, fallback=fallback))
        except ValueError:
            result = fallback

        return result

    def get_string_safe(self, section: str, option: str, fallback: str = "") -> str:
        """Returns config option as string or default if missing or empty"""
        result: str = super().get(section, option, fallback=fallback).strip("'\"")

        return result or fallback
