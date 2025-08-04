import os
from tkinter import Tk

import pytest
from PIL.Image import Image
from PIL.Image import new as new_image

from image_viewer.image.cache import ImageCache
from image_viewer.image.loader import ImageLoader
from image_viewer.image.resizer import ImageResizer
from image_viewer.ui.canvas import CustomCanvas
from tests.test_util.mocks import MockImage

WORKING_DIR: str = os.path.dirname(__file__)
IMG_DIR: str = os.path.join(WORKING_DIR, "example_images")
EXAMPLE_IMG_PATH: str = os.path.join(IMG_DIR, "a.png")
CODE_DIR: str = os.path.join(os.path.dirname(WORKING_DIR), "image_viewer")


@pytest.fixture
def image_resizer() -> ImageResizer:
    return ImageResizer(CODE_DIR, 1920, 1080)


@pytest.fixture
def image_cache() -> ImageCache:
    return ImageCache(20)


@pytest.fixture(scope="session")
def empty_image_cache() -> ImageCache:
    return ImageCache(0)


@pytest.fixture
def image_loader(image_cache: ImageCache) -> ImageLoader:
    image_loader = ImageLoader(CODE_DIR, 1920, 1080, image_cache, lambda *_: None)
    image_loader.PIL_image = MockImage()
    return image_loader


@pytest.fixture(scope="session")
def tk_app() -> Tk:
    app = Tk()
    app.withdraw()
    return app


@pytest.fixture
def canvas(tk_app) -> CustomCanvas:
    custom_canvas = CustomCanvas(tk_app, "#000000")
    custom_canvas.screen_height = 1080
    custom_canvas.screen_width = 1080
    return custom_canvas


@pytest.fixture(scope="session")
def example_image() -> Image:
    return new_image("RGB", (10, 10))
