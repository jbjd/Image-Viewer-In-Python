import os
from time import perf_counter
from image_viewer.util._os import get_files_in_folder, get_byte_display

path = "A:/hh/Imaj"
files = get_files_in_folder(path)
sizes = [os.stat(f"{path}/{b}").st_size for b in files]


# def get_byte_display(size_in_bytes: int) -> str:
#     """Given bytes, formats it into a string using kb or mb"""
#     kb_size: int = 1024 if os.name == "nt" else 1000
#     size_in_kb: int = size_in_bytes // kb_size
#     return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


a = perf_counter()

for size in sizes:
    get_byte_display(size)

print(perf_counter() - a)
