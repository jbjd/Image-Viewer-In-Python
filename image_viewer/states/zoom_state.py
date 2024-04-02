class ZoomState:

    ZOOM_CAP: int = 512

    __slots__ = "cap", "level"

    def __init__(self) -> None:
        self.cap: int = self.ZOOM_CAP
        self.level: int = 0

    def try_update_zoom_level(self, zoom_in: bool) -> bool:
        """Tries to zoom in or out. Returns True when zoom level changed"""
        previous_zoom: int = self.level

        if zoom_in and previous_zoom < self.cap:
            self.level += 1
        elif not zoom_in and previous_zoom > 0:
            self.level -= 1

        return previous_zoom != self.level

    def hit_cap(self) -> None:
        """Sets cap to the current zoom level"""
        self.cap = self.level

    def reset(self) -> None:
        """Resets zoom level"""
        self.cap = self.ZOOM_CAP
        self.level = 0

    def __eq__(self, __value: "ZoomState") -> bool:
        return self.level == __value.level and self.cap == __value.cap
