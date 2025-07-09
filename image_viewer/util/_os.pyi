import os

if os.name == "nt":
    def open_with(hwnd: int, file: str) -> None:
        """Calls SHOpenWithDialog without registration option
        on provided file"""

def get_files_in_folder(folder: str) -> list[str]:  # noqa: E302
    """Finds all files in the folder, not checking subfolders"""
