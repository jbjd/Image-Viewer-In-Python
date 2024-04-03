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
    EQUALS = 187
    MINUS = 189
    R = 82
