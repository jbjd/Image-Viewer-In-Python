import os
from tkinter import Tk
from unittest.mock import patch

import pytest
from PIL.Image import Image
from PIL.Image import new as new_image
from PIL.ImageTk import PhotoImage

from image_viewer.actions.undoer import ActionUndoer
from image_viewer.config import DEFAULT_FONT
from image_viewer.constants import Key
from image_viewer.files.file_manager import ImageFileManager
from image_viewer.image.cache import ImageCache
from image_viewer.image.file import ImageName, ImageNameList
from image_viewer.image.loader import ImageLoader
from image_viewer.image.resizer import ImageResizer
from image_viewer.state.zoom_state import ZoomState
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


@pytest.fixture(scope="module")
def button_icon_factory() -> ButtonIconFactory:
    return ButtonIconFactory(32)


@pytest.fixture
def image_cache() -> ImageCache:
    return ImageCache(20)


@pytest.fixture(scope="session")
def empty_image_cache() -> ImageCache:
    return ImageCache(0)


@pytest.fixture
def file_manager(image_cache: ImageCache) -> ImageFileManager:
    return ImageFileManager(EXAMPLE_IMG_PATH, image_cache)


@pytest.fixture
def file_manager_with_3_images(image_cache: ImageCache) -> ImageFileManager:
    manager = ImageFileManager(EXAMPLE_IMG_PATH, image_cache)
    manager._files = ImageNameList([*map(ImageName, ("a.png", "c.jpg", "e.webp"))])
    return manager


@pytest.fixture
def image_resizer() -> ImageResizer:
    return ImageResizer(CODE_DIR, 1920, 1080)


@pytest.fixture
def image_loader(image_cache: ImageCache) -> ImageLoader:
    image_loader = ImageLoader(CODE_DIR, 1920, 1080, image_cache, lambda *_: None)
    image_loader.PIL_image = MockImage()
    return image_loader


@pytest.fixture
def action_undoer() -> ActionUndoer:
    return ActionUndoer()


@pytest.fixture
def zoom_state() -> ZoomState:
    return ZoomState()


@pytest.fixture
def rename_entry(tk_app: Tk, canvas: CustomCanvas) -> RenameEntry:
    rename_id: int = canvas.create_window(
        0,
        0,
        width=250,
        height=20,
        anchor="nw",
    )
    return RenameEntry(tk_app, canvas, rename_id, 250, DEFAULT_FONT)


@pytest.fixture
def partial_viewer(tk_app: Tk, image_loader: ImageLoader, file_manager) -> ViewerApp:
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


@pytest.fixture(scope="module")
def focused_event(tk_app: Tk) -> MockEvent:
    return MockEvent(tk_app)


@pytest.fixture(scope="module")
def unfocused_event() -> MockEvent:
    return MockEvent()


@pytest.fixture(scope="module")
def left_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym_num=Key.LEFT)


@pytest.fixture(scope="module")
def right_key_event(tk_app):
    return MockEvent(widget=tk_app, keysym_num=Key.RIGHT)


@pytest.fixture(scope="session")
def example_image() -> Image:
    return new_image("RGB", (10, 10))


@pytest.fixture(scope="session")
def button_icons(example_image: Image) -> IconImages:
    default_icon = PhotoImage(example_image)
    hovered_icon = PhotoImage(example_image)
    return IconImages(default_icon, hovered_icon)
