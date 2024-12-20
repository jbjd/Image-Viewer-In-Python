from __future__ import annotations

from tkinter import Event, Tk
from typing import Self

from PIL.Image import Image

from image_viewer.actions.undoer import ActionUndoer, UndoResponse
from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.image import ImageName


class MockStatResult:
    """Mocks OS's stat_result"""

    st_ctime: int = 1649709119
    st_mtime: int = 1649709119

    def __init__(self, st_size: int) -> None:
        self.st_size: int = st_size


class MockEvent(Event):
    """Mocks Tk Event"""

    def __init__(self, widget: Tk | None = None, keycode: int = 0, x: int = 0) -> None:
        self.widget: Tk | None = widget
        self.keycode: int = keycode
        self.x: int = x


class MockImage(Image):
    """Mocks PIL Image for testing"""

    mode: str = "P"
    info: dict = {}
    _size: tuple[int, int] = (0, 0)

    def __init__(self, n_frames: int = 1, format: str = "") -> None:
        self.format: str = format
        self.n_frames: int = n_frames
        self.closed: bool = False

        if n_frames > 1:  # Like PIL, only set for animtions
            self.is_animated: bool = True

    def convert(self, new_mode: str) -> Self:  # type: ignore
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def close(self, *_) -> None:
        self.closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_) -> None:
        self.close()


class MockActionUndoer(ActionUndoer):
    """Mocks this module's ActionUndoer"""

    def undo(*_):
        return UndoResponse("b.png", "a.png")


class MockImageFileManager(ImageFileManager):
    """Mocks this module's ImageFileManager"""

    cache: dict = {}
    current_image = ImageName("test.png")
    path_to_image: str = ""

    def __init__(self) -> None:
        pass

    def remove_current_image(self) -> None:
        pass

    def current_image_cache_still_fresh(self) -> bool:
        return True
