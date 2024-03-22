import os
from tkinter import Tk

import pytest

from image_viewer.helpers.image_loader import ImageLoader
from image_viewer.helpers.image_resizer import ImageResizer
from image_viewer.ui.canvas import CustomCanvas
from test_util.mocks import MockImage, MockImageFileManager

WORKING_DIR: str = os.path.dirname(__file__)
IMG_DIR: str = os.path.join(WORKING_DIR, "example_images")


@pytest.fixture
def image_resizer() -> ImageResizer:
    return ImageResizer(
        1920, 1080, os.path.join(os.path.dirname(WORKING_DIR), "image_viewer")
    )


@pytest.fixture
def image_loader(image_resizer: ImageResizer) -> ImageLoader:
    image_loader = ImageLoader(MockImageFileManager(), image_resizer, lambda *_: None)
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
    custom_canvas.screen_height = 1080  # type: ignore
    custom_canvas.screen_width = 1080  # type: ignore
    return custom_canvas
