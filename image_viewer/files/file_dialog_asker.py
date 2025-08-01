"""
Logic for interacting with native file dialogs
"""

from tkinter.filedialog import askopenfilename
from typing import Iterable


class FileDialogAsker:
    """Handles asking user file dialogs"""

    __slots__ = ("_dialog_file_types",)

    def __init__(self, valid_file_types: Iterable[str]) -> None:
        self._dialog_file_types: list[tuple[str, str]] = [
            ("", f"*.{file_type}") for file_type in valid_file_types
        ]

    def ask_open_image(self, directory: str) -> str:
        """Ask user to choose an image file and returns its path"""

        return askopenfilename(
            title="Open Image",
            initialdir=directory,
            filetypes=self._dialog_file_types,
        )
