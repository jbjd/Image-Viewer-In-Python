"""Functions the help work with jpeg files"""

from typing import Callable

from PIL.Image import Image

def decode_scaled_jpeg(
    path: str,
    scale_factor: tuple[int, int],
    image_from_bytes: Callable[[str, tuple[int, int], bytes], None],
) -> Image | None:
    """Given a path, sc"""

del Callable
del Image
