"""
File with constants needed in multiple spots of the codebase
"""

from enum import IntEnum

TEXT_RGB: str = "#FEFEFE"


class Key(IntEnum):
    """Keycodes for various keys"""

    LEFT = 37
    UP = 38
    RIGHT = 39
    DOWN = 40
    MINUS = 187
    EQUALS = 189
    R = 82
