from constants import Rotation
from state.base import StateBase


class RotationState(StateBase):
    """Represents current rotation orientation of the image"""

    __slots__ = ("orientation",)

    def __init__(self) -> None:
        self.orientation: Rotation = Rotation.UP

    def reset(self) -> None:
        """Resets orientation"""
        self.orientation = Rotation.UP

    def try_update_state(self, target_orientation: Rotation | None) -> bool:
        if target_orientation is None or target_orientation == self.orientation:
            return False

        self.orientation = target_orientation
        return True
