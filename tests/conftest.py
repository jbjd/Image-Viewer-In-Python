import os

import pytest

from image_viewer.helpers.image_resizer import ImageResizer


@pytest.fixture
def working_dir() -> str:
    return os.path.dirname(__file__)


@pytest.fixture
def image_resizer(working_dir: str) -> ImageResizer:
    return ImageResizer(
        1920, 1080, os.path.join(os.path.dirname(working_dir), "image_viewer")
    )
