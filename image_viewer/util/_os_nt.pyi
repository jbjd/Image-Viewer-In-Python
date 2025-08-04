import os

if os.name == "nt":
    def trash_file(hwnd: int, file: str) -> None:
        """Moves provided file to trash"""

    def restore_file(hwnd: int, file: str) -> None:
        """Restores a file from recycling bin"""

    def get_files_in_folder(folder: str) -> list[str]:
        """Finds all files in the folder, not checking subfolders"""

    def get_byte_display(bytes: int) -> str:
        """Given the byte count, return how it should be displayed on screen"""

    def open_with(hwnd: int, file: str) -> None:
        """Calls SHOpenWithDialog without registration option
        on provided file"""

    def drop_file_to_clipboard(hwnd: int, file: str) -> None:
        """Copies a file to clipboard as an HDROP"""

    def convert_file_to_base64_and_save_to_clipboard(file: str) -> None:
        """Reads a file, converts it to base64, and copies it to clipboard"""
