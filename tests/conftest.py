import os
from tkinter import Tk

import pytest

from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.helpers.image_resizer import ImageResizer
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.util.image import ImageCache
from tests.test_util.mocks import MockImage

WORKING_DIR: str = os.path.dirname(__file__)
IMG_DIR: str = os.path.join(WORKING_DIR, "example_images")


@pytest.fixture
def image_resizer() -> ImageResizer:
    return ImageResizer(
        1920, 1080, os.path.join(os.path.dirname(WORKING_DIR), "image_viewer")
    )


@pytest.fixture
def image_cache() -> ImageCache:
    return ImageCache()


@pytest.fixture(scope="session")
def empty_image_cache() -> ImageCache:
    return ImageCache(0)


@pytest.fixture
def image_loader(image_resizer: ImageResizer, image_cache: ImageCache) -> ImageLoader:
    image_loader = ImageLoader(image_resizer, image_cache, lambda *_: None)
    image_loader.PIL_image = MockImage()
    return image_loader


@pytest.fixture(scope="session")
def tk_app() -> Tk:
    app = Tk()
    app.withdraw()
    return app


@pytest.fixture
def canvas(tk_app) -> CustomCanvas:
    custom_canvas = CustomCanvas(tk_app)
    custom_canvas.screen_height = 1080
    custom_canvas.screen_width = 1080
    return custom_canvas
