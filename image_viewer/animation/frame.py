"""Representations of frames of an animated image"""

from PIL.Image import Image

DEFAULT_ANIMATION_SPEED_MS: int = 100


class Frame:
    """A frame within an animated image"""

    __slots__ = ("image", "ms_until_next_frame")

    def __init__(self, image: Image) -> None:
        self.image: Image = image
        self.ms_until_next_frame: int = self.get_ms_until_next_frame(image)

    @staticmethod
    def get_ms_until_next_frame(image: Image) -> int:
        """Returns milliseconds until next frame for animated images"""

        ms: int = round(image.info.get("duration", DEFAULT_ANIMATION_SPEED_MS))
        return ms if ms > 1 else DEFAULT_ANIMATION_SPEED_MS
