import os
from time import perf_counter
from image_viewer.util._os_nt import get_files_in_folder

# path = "A:/hh/Imaj"
# files = get_files_in_folder(path)
# sizes = [os.stat(f"{path}/{b}").st_size for b in files]

hex_to_test = [
    f"#{os.urandom(3).hex()}" if i % 2 == 0 else f"#{os.urandom(1).hex()}zggg"
    for i in range(999999)
]

# def get_byte_display(size_in_bytes: int) -> str:
#     """Given bytes, formats it into a string using kb or mb"""
#     kb_size: int = 1024 if os.name == "nt" else 1000
#     size_in_kb: int = size_in_bytes // kb_size
#     return f"{size_in_kb/kb_size:.2f}mb" if size_in_kb > 999 else f"{size_in_kb}kb"


# def is_hex(hex_code: str):
#     return (
#         len(hex_code) == 7
#         and hex_code[0] == "#"
#         and all(hex_code[index] in "0123456789abcdefABCDEF" for index in range(1, 7))
#     )


# def validate_hex_or_default(hex_code: str, default: str) -> str:
#     if is_hex(hex_code):
#         return hex_code

#     return default


def validate_hex_or_default(hex_code: str, default: str) -> str:
    """Returns hex_code if its in the valid hex format or default if not"""
    if (
        len(hex_code) == 7
        and hex_code[0] == "#"
        and all(hex_code[index] in "0123456789abcdefABCDEF" for index in range(1, 7))
    ):
        return hex_code

    return default


a = perf_counter()

for hex in hex_to_test:
    validate_hex_or_default(hex, "#000000")

print(perf_counter() - a)
