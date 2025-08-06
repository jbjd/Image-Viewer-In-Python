"""Classes that represent the zoom state"""

from constants import ZoomDirection
from state.base import StateBase


class ZoomState(StateBase):
    """Represents level of zoom and stores max zoom level"""

    ZOOM_CAP: int = 64

    __slots__ = ("_max_level", "level")

    def __init__(self) -> None:
        self.level: int = 0
        self._max_level: int = self.ZOOM_CAP

    def reset(self) -> None:
        """Resets zoom level"""
        self.level = 0
        self._max_level = self.ZOOM_CAP

    def try_update_zoom_level(self, direction: ZoomDirection | None) -> bool:
        """Tries to zoom in or out. Returns True if zoom level changed"""
        if direction is None:
            return False

        previous_zoom: int = self.level

        if direction == ZoomDirection.IN and previous_zoom < self._max_level:
            self.level += 1
        elif direction == ZoomDirection.OUT and previous_zoom > 0:
            self.level -= 1

        return previous_zoom != self.level

    def set_current_zoom_level_as_max(self) -> None:
        """Sets cap to the current zoom level"""
        self._max_level = self.level
