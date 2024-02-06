from tkinter import Entry, Tk, StringVar


class RenameEntry(Entry):
    """Entry for use in a rename window"""

    BG_COLOR: str = "#FEFEFE"
    ERROR_COLOR: str = "#E6505F"

    __slots__ = ("id", "max_width", "text")

    def __init__(self, master: Tk, id: int, max_width: int, font: str) -> None:
        self.text = StringVar()
        self.id: int = id
        self.max_width: int = max_width

        super().__init__(
            master, font=font, bg=self.BG_COLOR, borderwidth=0, textvariable=self.text
        )

        # ensure ctrl+c is processed outside of this program
        self.bind("<Control-c>", lambda _: self.master.update(), True)

    def get(self) -> str:
        """Gets stripped text from Entry"""
        return super().get().strip()

    def error_flash(self) -> None:
        """Makes Entry flash red"""
        self.config(bg=self.ERROR_COLOR)
        self.master.after(400, lambda: self.config(bg=self.BG_COLOR))
