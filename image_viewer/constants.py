"""
File with constants needed in multiple spots of the codebase
"""

from enum import IntEnum, StrEnum


class ImageFormats(StrEnum):
    """Image format strings that this app supports"""

    AVIF = "AVIF"
    DDS = "DDS"
    GIF = "GIF"
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WebP"


class Key(IntEnum):
    """Keysym numbers for various keys"""

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


VALID_FILE_TYPES: set[str] = {
    "avif",
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


TEXT_RGB: str = "#FEFEFE"
