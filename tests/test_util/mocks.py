from __future__ import annotations

from tkinter import Event

from PIL.Image import Image

from image_viewer.util.action_undoer import ActionUndoer


class MockImage(Image):
    """Mocks PIL Image for testing"""

    mode: str = "P"
    info: dict = {}

    def __init__(self, n_frames: int = 1) -> None:
        self.n_frames: int = n_frames

        if n_frames > 1:  # Like PIL, only set for animtions
            self.is_animated = True

    def convert(self, new_mode: str) -> MockImage:
        self.mode = new_mode
        return self

    def save(self, *_, **kwargs) -> None:
        pass

    def __enter__(self) -> MockImage:
        return self

    def __exit__(self, *_) -> None:
        pass


class MockEvent(Event):
    """Mocks Tk Event"""

    def __init__(self, x: int) -> None:
        self.x: int = x


class MockActionUndoer(ActionUndoer):
    """Mocks this module's ActionUndoer"""

    def undo(*_):
        return ("b.png", "a.png")
