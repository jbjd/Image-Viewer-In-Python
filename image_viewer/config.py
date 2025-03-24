"""
Reads config.ini from root directory and stores results or defaults
"""

import os
import re
from configparser import ConfigParser

from constants import DEFAULT_FONT, DEFAULT_MAX_ITEMS_IN_CACHE, DefaultKeybinds


class Config:
    """Reads configs from config.ini"""

    __slots__ = ("font_file", "keybinds", "max_items_in_cache")

    def __init__(
        self, working_directory: str, config_file_name: str = "config.ini"
    ) -> None:
        config_parser: ConfigParser = ConfigParser()
        config_parser.read(os.path.join(working_directory, config_file_name))

        self.font_file: str = (
            config_parser.get("FONT", "DEFAULT", fallback=DEFAULT_FONT) or DEFAULT_FONT
        )
        self.max_items_in_cache: int
        try:
            self.max_items_in_cache = int(
                config_parser.get("CACHE", "SIZE", fallback=DEFAULT_MAX_ITEMS_IN_CACHE)
            )
        except ValueError:
            self.max_items_in_cache = DEFAULT_MAX_ITEMS_IN_CACHE

        self.keybinds = KeybindConfig(
            config_parser.get("KEYBINDS", "SHOW_DETAILS", fallback="")
        )


class KeybindConfig:
    """Contains configurable tkinter keybinds"""

    __slots__ = ("show_details",)

    def __init__(self, show_details: str) -> None:
        self.show_details = validate_or_default(
            show_details, DefaultKeybinds.SHOW_DETAILS
        )


def validate_or_default(keybind: str, default: str) -> str:
    """Given a tkinter keybind, validate if its allowed
    and return keybind if its valid or the default if its not"""
    f_key_re = r"F([1-9]|10|11|12)"
    control_key_re = r"Control-[a-zA-Z0-9]"

    match = re.match(f"^<(({f_key_re})|({control_key_re}))>$", keybind)

    return default if match is None else keybind
