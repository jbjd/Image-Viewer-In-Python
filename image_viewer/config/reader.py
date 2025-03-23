"""
Reads config.ini from root directory and stores results or defaults
"""

import os
from configparser import ConfigParser

from config.validate import validate_or_default
from constants import DEFAULT_FONT, DEFAULT_MAX_ITEMS_IN_CACHE, DefaultKeybinds


class ConfigReader:
    """Reads configs from config.ini"""

    __slots__ = ("font_file", "keybinds", "max_items_in_cache")

    def __init__(self, path_to_exe_folder: str) -> None:
        config_parser: ConfigParser = ConfigParser()
        config_parser.read(os.path.join(path_to_exe_folder, "config.ini"))

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
