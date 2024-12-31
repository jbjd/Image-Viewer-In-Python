"""
File with constants needed in multiple spots of the codebase
"""

import os
from enum import IntEnum, StrEnum
from typing import Final


class ImageFormats(StrEnum):
    DDS = "DDS"
    GIF = "GIF"
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WebP"


class Key(StrEnum):
    """Keysyms for various keys"""

    LEFT = "Left"
    RIGHT = "Right"
    EQUALS = "equal"
    MINUS = "minus"
    R = "r"


class Rotation(IntEnum):
    """Denotes angle of rotation"""

    LEFT = 90
    RIGHT = 270
    FLIP = 180


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


DEFAULT_FONT: Final[str] = (
    "arial.ttf" if os.name == "nt" else "LiberationSans-Regular.ttf"
)
DEFAULT_MAX_ITEMS_IN_CACHE: Final[int] = 20

TEXT_RGB: str = "#FEFEFE"
