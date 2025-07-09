import os

if os.name == "nt":
    def open_with(hwnd: int, file: str) -> None: ...

def get_files_in_folder(folder: str) -> list[str]: ...  # noqa: E302
