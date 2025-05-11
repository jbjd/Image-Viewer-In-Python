"""
File with constants needed in multiple spots of the codebase
"""

import os
from enum import IntEnum, StrEnum
from typing import Final


class ImageFormats(StrEnum):
    """Image format strings that this app supports"""

    DDS = "DDS"
    GIF = "GIF"
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WebP"


class Key(IntEnum):
    """Keysym numbers for various keys"""

    MINUS = 45
    EQUALS = 61
    LEFT = 65361
    RIGHT = 65363
    DOWN = 65364


class Rotation(IntEnum):
    """Denotes angle of rotation"""

    UP = 0
    LEFT = 90
    DOWN = 180
    RIGHT = 270


class ZoomDirection(IntEnum):
    """Either up or down on the mouse wheel"""

    IN = 1
    OUT = -1


class TkTags(StrEnum):
    """Tags for items on the UI"""

    TOPBAR = "topbar"
    BACKGROUND = "back"


class ButtonName(StrEnum):
    """Names of buttons on the UI"""

    EXIT = "exit"
    MINIFY = "minify"
    TRASH = "trash"
    RENAME = "rename"
    DROPDOWN = "dropdown"


class DefaultKeybinds(StrEnum):
    """Defaults for keybinds that config.ini can override"""

    MOVE_TO_NEW_FILE = "<Control-m>"
    SHOW_DETAILS = "<Control-d>"
    UNDO_MOST_RECENT_ACTION = "<Control-z>"


VALID_FILE_TYPES: set[str] = {
    "gif",
    "jpg",
    "jpeg",
    "jpe",
    "jfif",
    "jif",
    "png",
    "webp",
    "dds",
}

DEFAULT_BACKGROUND_COLOR: Final[str] = "#000000"
DEFAULT_FONT: Final[str] = (
    "arial.ttf" if os.name == "nt" else "LiberationSans-Regular.ttf"
)
DEFAULT_MAX_ITEMS_IN_CACHE: Final[int] = 20

TEXT_RGB: str = "#FEFEFE"
