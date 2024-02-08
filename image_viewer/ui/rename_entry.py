from tkinter import Canvas, Entry, Event, Tk


class RenameEntry(Entry):
    """Entry for use in a rename window"""

    BG_COLOR: str = "#FEFEFE"
    ERROR_COLOR: str = "#E6505F"

    __slots__ = ("being_resized", "cursor", "id", "min_width", "text")

    def __init__(
        self, master: Tk, canvas: Canvas, id: int, min_width: int, font: str
    ) -> None:
        super().__init__(
            master,
            font=font,
            bg=self.BG_COLOR,
            disabledbackground=self.BG_COLOR,
            fg="black",
            disabledforeground="black",
            borderwidth=0,
            width=min_width,
        )

        self.id: int = id
        self.min_width: int = min_width

        self.being_resized: bool = False
        self.cursor: str = ""

        # ensure ctrl+c is processed outside of this program
        self.bind("<Control-c>", lambda _: self.master.update(), True)
        self.bind("<ButtonPress-1>", self._try_start_resize)
        self.bind("<ButtonRelease-1>", self._stop_resize)
        self.bind("<Motion>", lambda e: self._resize(canvas, e))

    def can_resize(self, event: Event) -> bool:
        width = self.cget("width")
        if event.x >= width - (self.min_width // 35):
            return True
        return False

    def _try_start_resize(self, event: Event) -> None:
        self.being_resized = self.can_resize(event)

    def _stop_resize(self, _: Event) -> None:
        self.config(state="normal")
        self.being_resized = False

    def _resize(self, canvas: Canvas, event: Event) -> None:
        """Handles user draggig to resize rename window"""
        if self.being_resized:
            self.config(state="disabled")
            new_width: int = event.x
            if (new_width >= self.min_width) and (new_width <= (self.min_width << 1)):
                self.config(width=new_width)
                canvas.itemconfig(self.id, width=new_width)
        else:
            cursor = "sb_h_double_arrow" if self.can_resize(event) else ""
            if cursor != self.cursor:
                self.config(cursor=cursor)
                self.cursor = cursor

    def get(self) -> str:
        """Gets stripped text from Entry"""
        return super().get().strip()

    def error_flash(self) -> None:
        """Makes Entry flash red"""
        self.config(bg=self.ERROR_COLOR)
        self.master.after(400, lambda: self.config(bg=self.BG_COLOR))
