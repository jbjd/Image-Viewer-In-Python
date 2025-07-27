import os

if os.name == "posix":
    def convert_file_to_base64_and_save_to_clipboard(file: str) -> None:
        """Reads a file, converts it to base64, and copies it to clipboard"""
