import os
from time import perf_counter

# from image_viewer.util._generic import is_hex

hex_to_test = [
    f"#{os.urandom(3).hex()}"  # if i % 2 == 0 else f"#{os.urandom(1).hex()}zggg"
    for i in range(999999)
]


def is_hex(hex):
    return (
        len(hex) == 7
        and hex[0] == "#"
        and all(hex[index] in "0123456789abcdefABCDEF" for index in range(1, 7))
    )


def validate_hex_or_default(hex_code: str, default: str) -> str:
    if is_hex(hex_code):
        return hex_code

    return default


a = perf_counter()

for hex in hex_to_test:
    validate_hex_or_default(hex, "#000000")

print(perf_counter() - a)
