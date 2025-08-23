"""Common file for pytest framework to define test fixtures, also used to
define other constants used within tests"""

import os
from tkinter import Tk
from unittest.mock import patch

import pytest
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.ImageTk import PhotoImage

from image_viewer.config import DEFAULT_FONT
from image_viewer.files.file_manager import ImageFileManager
from image_viewer.image.cache import ImageCache
from image_viewer.image.file import ImageName, ImageNameList
from image_viewer.image.loader import ImageLoader
from image_viewer.image.resizer import ImageResizer
from image_viewer.ui.button import IconImages
from image_viewer.ui.button_icon_factory import ButtonIconFactory
from image_viewer.ui.canvas import CustomCanvas
from image_viewer.ui.rename_entry import RenameEntry
from image_viewer.viewer import ViewerApp
from tests.test_util.mocks import MockEvent, MockImage

WORKING_DIR: str = os.path.dirname(__file__)
IMG_DIR: str = os.path.join(WORKING_DIR, "example_images")
EXAMPLE_IMG_PATH: str = os.path.join(IMG_DIR, "a.png")
CODE_DIR: str = os.path.join(os.path.dirname(WORKING_DIR), "image_viewer")


@pytest.fixture(name="tk_app", scope="session")
def tk_app_fixture() -> Tk:
    app = Tk()
    app.withdraw()
    return app


@pytest.fixture(name="canvas")
def canvas_fixture(tk_app) -> CustomCanvas:
    custom_canvas = CustomCanvas(tk_app, "#000000")
    custom_canvas.screen_height = 1080
    custom_canvas.screen_width = 1080
    return custom_canvas


@pytest.fixture(name="button_icon_factory", scope="module")
def button_icon_factory_fixture() -> ButtonIconFactory:
    return ButtonIconFactory(32)


@pytest.fixture(name="image_cache")
def image_cache_fixture() -> ImageCache:
    return ImageCache(20)


@pytest.fixture(name="file_manager")
def file_manager_fixture(image_cache: ImageCache) -> ImageFileManager:
    return ImageFileManager(EXAMPLE_IMG_PATH, image_cache)


@pytest.fixture(name="file_manager_with_3_images")
def file_manager_with_3_images_fixture(image_cache: ImageCache) -> ImageFileManager:
    manager = ImageFileManager(EXAMPLE_IMG_PATH, image_cache)
    manager._files = ImageNameList([*map(ImageName, ("a.png", "c.jpg", "e.webp"))])
    return manager


@pytest.fixture(name="image_resizer")
def image_resizer_fixture() -> ImageResizer:
    return ImageResizer(1920, 1080)


@pytest.fixture(name="image_loader")
def image_loader_fixture(image_cache: ImageCache) -> ImageLoader:
    image_loader = ImageLoader(1920, 1080, image_cache, lambda *_: None)
    image_loader.PIL_image = MockImage()
    return image_loader


@pytest.fixture(name="rename_entry")
def rename_entry_fixture(tk_app: Tk, canvas: CustomCanvas) -> RenameEntry:
    rename_id: int = canvas.create_window(
        0,
        0,
        width=250,
        height=20,
        anchor="nw",
    )
    return RenameEntry(tk_app, canvas, rename_id, 250, DEFAULT_FONT)


@pytest.fixture(name="partial_viewer")
def partial_viewer_fixture(
    tk_app: Tk, image_loader: ImageLoader, file_manager
) -> ViewerApp:
    """A Viewer object that's not properly initialized.
    Can be used to test standalone parts of the class"""

    def mock_viewer_init(self, *_):
        self.app = tk_app
        self.file_manager = file_manager
        self.image_loader = image_loader
        self.animation_id = ""
        self.move_id = ""
        self.need_to_redraw = False

    with patch.object(ViewerApp, "__init__", mock_viewer_init):
        return ViewerApp("", "")


@pytest.fixture(name="focused_event", scope="module")
def focused_event_fixture(tk_app: Tk) -> MockEvent:
    return MockEvent(tk_app)


@pytest.fixture(name="unfocused_event", scope="module")
def unfocused_event_fixture() -> MockEvent:
    return MockEvent()


@pytest.fixture(name="example_image", scope="session")
def example_image_fixture() -> Image:
    return new_image("RGB", (10, 10))


@pytest.fixture(name="button_icons", scope="session")
def button_icons_fixture(example_image: Image) -> IconImages:
    default_icon = PhotoImage(example_image)
    hovered_icon = PhotoImage(example_image)
    return IconImages(default_icon, hovered_icon)
