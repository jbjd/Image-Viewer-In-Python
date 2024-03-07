import os
from tkinter import Tk

import pytest

from image_viewer.helpers.image_resizer import ImageResizer
from image_viewer.ui.canvas import CustomCanvas

WORKING_DIR: str = os.path.dirname(__file__)


@pytest.fixture
def img_dir() -> str:
    return os.path.join(WORKING_DIR, "example_images")


@pytest.fixture
def image_resizer() -> ImageResizer:
    return ImageResizer(
        1920, 1080, os.path.join(os.path.dirname(WORKING_DIR), "image_viewer")
    )


@pytest.fixture(scope="session")
def tk_app() -> Tk:
    app = Tk()
    app.withdraw()
    return app


@pytest.fixture
def canvas(tk_app) -> CustomCanvas:
    return CustomCanvas(tk_app)
