"""Functions the help work with jpeg files"""

from typing import Callable

from PIL.Image import Image

class CMemoryViewBuffer:
    """Contains a memoryview object to malloc'ed C data.
    Only intended to be created within C code and consumed by Python code"""

    __slots__ = ("buffer_view",)

    buffer_view: memoryview

class CMemoryViewBufferJpeg(CMemoryViewBuffer):
    """Contains a memoryview object to malloc'ed C data containing a JPEG.
    Only intended to be created within C code and consumed by Python code"""

    __slots__ = ("dimensions",)

    dimensions: tuple[int, int]

def read_image_into_buffer(image_path: str) -> CMemoryViewBuffer | None:
    """Returns am image's bytes as a CMemoryViewBuffer or None if an error occurred
    while reading the file"""

def decode_scaled_jpeg(
    image_bytes: CMemoryViewBuffer, scale_factor: tuple[int, int]
) -> CMemoryViewBufferJpeg:
    """Given an image's bytes, decode them as a scaled jpeg and return its bytes as a CMemoryViewBuffer
    or None if reading the image failed"""

del Callable
del Image
