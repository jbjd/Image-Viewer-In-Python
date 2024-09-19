from tkinter import Canvas, Entry, Event, Tk
from typing import Literal

from constants import TEXT_RGB


class RenameEntry(Entry):  # pylint: disable=too-many-ancestors
    """Entry for use in a rename window"""

    ERROR_COLOR: str = "#E6505F"

    __slots__ = ("being_resized", "canvas_id", "cursor", "min_width", "text")

    def __init__(
        self, master: Tk, canvas: Canvas, canvas_id: int, min_width: int, font: str
    ) -> None:
        super().__init__(
            master,
            font=font,
            bg=TEXT_RGB,
            disabledbackground=TEXT_RGB,
            fg="black",
            disabledforeground="black",
            borderwidth=0,
            width=min_width,
        )
        canvas.itemconfigure(canvas_id, state="hidden", window=self)

        self.being_resized: bool = False
        self.cursor: str = ""
        self.id: int = canvas_id
        self.min_width: int = min_width

        # ensure ctrl+c is processed outside of this program
        self.bind("<Control-c>", lambda _: self.master.update(), True)
        self.bind("<ButtonPress-1>", self._start_resize)
        self.bind("<ButtonRelease-1>", self._stop_resize)
        self.bind("<Motion>", lambda e: self._resize(canvas, e.x))

    def mouse_can_resize(self, x_position: int) -> bool:
        """Returns True if x position on right edge of entry where user can resize"""
        width: int = self.cget("width")
        grabbable_x_width: int = self.min_width // 35

        return x_position >= width - grabbable_x_width

    def _start_resize(self, event: Event) -> None:
        """Starts resize if cursor is in the correct spot"""
        self.being_resized = self.mouse_can_resize(event.x)

    def _stop_resize(self, _: Event) -> None:
        """Reallows input when resize event ends"""
        self.config(state="normal")
        self.being_resized = False

    def _resize(self, canvas: Canvas, new_width: int) -> None:
        """Handles dragging to resize rename window"""
        if self.being_resized:
            self.config(state="disabled")
            max_width: int = self.min_width << 1
            if self.min_width <= new_width <= max_width:
                self.config(width=new_width)
                canvas.itemconfig(self.id, width=new_width)
        else:
            cursor: Literal["sb_h_double_arrow", ""] = (
                "sb_h_double_arrow" if self.mouse_can_resize(new_width) else ""
            )
            if cursor != self.cursor:
                self.config(cursor=cursor)
                self.cursor = cursor

    def get(self) -> str:
        """Gets stripped text from Entry"""
        return super().get().strip()

    def error_flash(self) -> None:
        """Makes Entry flash red"""
        self.config(bg=self.ERROR_COLOR)
        self.master.after(400, lambda: self.config(bg=TEXT_RGB))
