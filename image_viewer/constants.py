"""
File with constants needed in multiple spots of the codebase
"""

from enum import IntEnum

TOPBAR_TAG: str = "topbar"

TEXT_RGB: str = "#FEFEFE"


class Key(IntEnum):
    """Keycodes for various keys"""

    LEFT = 37
    UP = 38
    RIGHT = 39
    DOWN = 40
    R = 82


class Rotation(IntEnum):
    """Denotes angle of rotation"""

    LEFT = 90
    RIGHT = 270
    FLIP = 180


class MouseWheelDirection(IntEnum):
    """Either up or down on the mouse wheel"""

    UP = 1
    DOWN = -1
