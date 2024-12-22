"""Base classes for UI elements"""

from abc import ABC, abstractmethod
from tkinter import Event


class ButtonUIElementBase(ABC):
    """Base class for buttons to be used in a Tkinter UI"""

    def __init__(self) -> None:
        self.id: int = -1

    @abstractmethod
    def on_click(self, event: Event | None = None) -> None:
        pass

    def on_enter(self, _: Event | None = None) -> None:
        pass

    def on_leave(self, _: Event | None = None) -> None:
        pass
