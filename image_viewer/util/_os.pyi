import os

if os.name == "nt":
    def delete_file(hwnd: int, file: str) -> None:
        """Moves provided file to trash"""

    def get_files_in_folder(folder: str) -> list[str]:
        """Finds all files in the folder, not checking subfolders"""

    def open_with(hwnd: int, file: str) -> None:
        """Calls SHOpenWithDialog without registration option
        on provided file"""

    def drop_file_to_clipboard(hwnd: int, file: str) -> None:
        """Copies a file to clipboard as an HDROP"""
