from __future__ import annotations

from tkinter import Event

from PIL.Image import Image
from PIL.ImageTk import PhotoImage

from image_viewer.managers.file_manager import ImageFileManager
from image_viewer.util.action_undoer import ActionUndoer


class MockStatResult:
    """Mocks OS's stat_result"""

    def __init__(self, st_size: int) -> None:
        self.st_size: int = st_size


class MockEvent(Event):
    """Mocks Tk Event"""

    def __init__(self, x: int) -> None:
        self.x: int = x


class MockImage(Image):
    """Mocks PIL Image for testing"""

    mode: str = "P"
    info: dict = {}

    def __init__(self, n_frames: int = 1) -> None:
        self.n_frames: int = n_frames

        if n_frames > 1:  # Like PIL, only set for animtions
            self.is_animated: bool = True

    def convert(self, new_mode: str) -> MockImage:  # type: ignore
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass


class MockPhotoImage(PhotoImage):
    """Mocks PIL's PhotoImage"""

    def __init__(self) -> None:
        pass


class MockActionUndoer(ActionUndoer):
    """Mocks this module's ActionUndoer"""

    def undo(*_):
        return ("b.png", "a.png")


class MockImageFileManager(ImageFileManager):
    """Mocks this module's ImageFileManager"""

    def __init__(self) -> None:
        self.path_to_current_image = ""
