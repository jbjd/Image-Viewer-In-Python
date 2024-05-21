class ZoomState:

    ZOOM_DELTA: float = 1.1

    __slots__ = "zoom_scale", "level", "level_cap"

    def __init__(self) -> None:
        self.zoom_scale: float = 1
        self.level: int = 0
        self.level_cap: int = 1024

    def try_update_zoom_level(self, zoom_change_amount: int) -> bool:
        """Updates zoom level without allowing zoom smaller than initial size
        Returns True when zoom level was updated"""
        if zoom_change_amount == 0:
            return False

        previous_level: int = self.level
        self.level += zoom_change_amount
        if self.level < 0:
            self.level = 0

        zoom_did_not_changed: bool = self.level == previous_level
        if zoom_did_not_changed:
            return False

        if zoom_change_amount > 0:
            self.zoom_scale *= self.ZOOM_DELTA
        else:
            self.zoom_scale /= self.ZOOM_DELTA

        return True

    def reset(self) -> None:
        """Resets zoom level"""
        self.zoom_scale = 1
        self.level = 0
        self.level_cap = 1024
