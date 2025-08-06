from time import perf_counter
from image_viewer.util._generic import is_valid_keybind

tests = [
    "asdvbiu34uiyg",
    "<Control-d>",
    "<Control->",
    "<F0>",
    "<F1>",
    "<F12>",
    "<F13>",
    "<F91>",
] * 99999


def validate_keybind_or_default(keybind, default):

    return keybind if is_valid_keybind(keybind) else default


a = perf_counter()

for test in tests:
    validate_keybind_or_default(test, "something")

print(perf_counter() - a)
