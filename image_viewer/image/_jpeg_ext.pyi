"""Functions the help work with jpeg files"""

from typing import Callable

from PIL.Image import Image

class CMemoryViewBuffer:
    """Wraps a memoryview object to malloc'ed C data.
    Only intended to be created within C code and consumed by Python code"""

    __slots__ = ("buffer_view",)

    buffer_view: memoryview

def read_image_into_buffer(image_path: str) -> CMemoryViewBuffer | None:
    """Returns am image's bytes as a CMemoryViewBuffer or None if an error occurred
    while reading the file"""

def decode_scaled_jpeg(
    path: str,
    scale_factor: tuple[int, int],
    image_from_bytes: Callable[[str, tuple[int, int], bytes], None],
) -> Image | None:
    """Given a path, sc"""

del Callable
del Image
