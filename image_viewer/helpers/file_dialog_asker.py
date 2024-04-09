from typing import Iterable

from tkinter.filedialog import askopenfilename


class FileDialogAsker:
    """Handles asking user file dialogs"""

    __slots__ = "dialog_file_types"

    def __init__(self, valid_file_types: Iterable[str]) -> None:
        self.dialog_file_types = [
            ("", f"*.{file_type}") for file_type in valid_file_types
        ]

    def ask_open_image(self, directory: str) -> str:
        """Ask user to choose an image file and returns its path"""

        return askopenfilename(
            title="Open Image",
            initialdir=directory,
            filetypes=self.dialog_file_types,
        )