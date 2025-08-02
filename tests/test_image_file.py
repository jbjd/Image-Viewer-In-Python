import pytest

from image_viewer.constants import ImageFormats
from image_viewer.image.file import magic_number_guess


@pytest.mark.parametrize(
    "magic_bytes,expected_format",
    [
        (b"\x89PNG", ImageFormats.PNG),
        (b"RIFF", ImageFormats.WEBP),
        (b"GIF8", ImageFormats.GIF),
        (b"DDS ", ImageFormats.DDS),
        (b"\xff\xd8\xff\xe0", ImageFormats.JPEG),
        (b"\xff\xd8\xff\xed", ImageFormats.JPEG),
        (b"ABCD", ImageFormats.AVIF),  # default to AVIF
    ],
)
def test_magic_number_guess(magic_bytes: bytes, expected_format: ImageFormats):
    """Ensure correct image type guessed"""
    assert magic_number_guess(magic_bytes) == expected_format
