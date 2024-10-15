from PIL.Image import Image

DEFAULT_ANIMATION_SPEED_MS: int = 100


class Frame:
    """A frame within an animated image"""

    __slots__ = ("image", "ms_until_next_frame")

    def __init__(self, image: Image | None = None) -> None:
        self.image: Image | None = image
        self.ms_until_next_frame: int = self.get_ms_until_next_frame(image)

    @staticmethod
    def get_ms_until_next_frame(image: Image | None) -> int:
        """Returns milliseconds until next frame for animated images"""
        if image is None:
            return 0

        ms: int = round(image.info.get("duration", DEFAULT_ANIMATION_SPEED_MS))
        return ms if ms > 1 else DEFAULT_ANIMATION_SPEED_MS
