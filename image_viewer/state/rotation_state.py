from constants import Rotation
from state.base import StateBase


class RotationState(StateBase):
    """Represents current rotation orientation of image"""

    __slots__ = ("orientation",)

    def __init__(self) -> None:
        self.orientation: Rotation = Rotation.UP

    def reset(self) -> None:
        """Resets zoom level"""
        self.orientation = Rotation.UP
