from constants import ZoomDirection


class ZoomState:

    ZOOM_DELTA: float = 1.1

    __slots__ = "zoom_scale", "level", "level_cap"

    def __init__(self) -> None:
        self.zoom_scale: float = 1
        self.level: int = 0
        self.level_cap: int = 1024

    def try_update_zoom_level(self, direction: ZoomDirection) -> bool:
        """Tries to zoom in or out. Returns True when zoom level changed"""
        previous_level: int = self.level

        if direction == ZoomDirection.IN:
            self.level += 1
        elif direction == ZoomDirection.OUT and previous_level > 0:
            self.level -= 1

        zoom_did_not_changed: bool = self.level == previous_level
        if zoom_did_not_changed:
            return False

        if direction == ZoomDirection.IN:
            self.zoom_scale *= self.ZOOM_DELTA
        else:
            self.zoom_scale /= self.ZOOM_DELTA

        return True

    def reset(self) -> None:
        """Resets zoom level"""
        self.zoom_scale = 1
        self.level = 0
        self.level_cap = 1024
