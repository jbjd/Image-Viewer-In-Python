"""Base classes for UI elements"""

from abc import ABC, abstractmethod
from tkinter import Event


class UIElementBase(ABC):
    """Base class for any element on a tkinter canvas"""

    __slots__ = ("id",)

    def __init__(self, id: int = -1) -> None:
        self.id: int = id


class ButtonUIElementBase(UIElementBase):
    """Base class for buttons on a tkinter canvas"""

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def on_click(self, event: Event | None = None) -> None:
        pass

    def on_enter(self, _: Event | None = None) -> None:
        pass

    def on_leave(self, _: Event | None = None) -> None:
        pass
