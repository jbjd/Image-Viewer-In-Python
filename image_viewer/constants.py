"""
File with constants needed in multiple spots of the codebase
"""

from enum import IntEnum, StrEnum


class Key(IntEnum):
    """Keycodes for various keys"""

    LEFT = 37
    UP = 38
    RIGHT = 39
    DOWN = 40
    EQUALS = 187
    MINUS = 189
    R = 82


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


# TODO: Below, these could be configurable
TEXT_RGB: str = "#FEFEFE"

MAX_ITEMS_IN_CACHE: int = 20
