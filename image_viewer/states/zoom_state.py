class ZoomState:

    ZOOM_DELTA: float = 1.3

    __slots__ = "zoom_scale", "level", "level_cap"

    def __init__(self) -> None:
        self.zoom_scale: float = 1
        self.level: int = 0
        self.level_cap: int = 1024

    def try_update_zoom_level(self, zoom_in: bool) -> bool:
        """Updates zoom level and scale within bounds of upper cap and
        never allows zooming out more than initial size"""
        previous_level: int = self.level

        if zoom_in:
            self.level += 1
            self.zoom_scale *= self.ZOOM_DELTA
        elif self.level > 0:
            self.level -= 1
            self.zoom_scale /= self.ZOOM_DELTA

        return self.level != previous_level

    def reset(self) -> None:
        """Resets zoom level"""
        self.zoom_scale = 1
        self.level = 0
        self.level_cap = 1024
