"""
Reads config.ini from root dir and stores vars with results or defaults
"""

import os
import sys
from configparser import ConfigParser

from constants import DEFAULT_FONT, DEFAULT_MAX_ITEMS_IN_CACHE


class Config:
    """Loads configs from config.ini"""

    __slots__ = ("font_file", "max_items_in_cache")

    def __init__(self) -> None:
        config: ConfigParser = ConfigParser()
        config.read(os.path.join(os.path.dirname(sys.argv[0]), "config.ini"))

        self.font_file: str = (
            config.get("FONT", "DEFAULT", fallback=DEFAULT_FONT) or DEFAULT_FONT
        )
        self.max_items_in_cache: int
        try:
            self.max_items_in_cache = int(
                config.get("CACHE", "SIZE", fallback=DEFAULT_MAX_ITEMS_IN_CACHE)
            )
        except ValueError:
            self.max_items_in_cache = DEFAULT_MAX_ITEMS_IN_CACHE
