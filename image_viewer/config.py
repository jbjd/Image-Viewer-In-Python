"""
Reads config.ini from root dir and stores vars with results or defaults
"""

import os
import sys
from configparser import ConfigParser

from constants import DEFAULT_FONT, DEFAULT_MAX_ITEMS_IN_CACHE

_config: ConfigParser = ConfigParser()
_config.read(os.path.join(os.path.dirname(sys.argv[0]), "config.ini"))

# can't set DEFAULT_FONT to fallback, if user leaves DEFAULT empty
# get does not override it with fallback  value
font: str = _config.get("FONT", "DEFAULT", fallback=DEFAULT_FONT) or DEFAULT_FONT

try:
    max_items_in_cache: int = int(
        _config.get("CACHE", "SIZE", fallback=DEFAULT_MAX_ITEMS_IN_CACHE)
    )
except ValueError:
    max_items_in_cache = DEFAULT_MAX_ITEMS_IN_CACHE
