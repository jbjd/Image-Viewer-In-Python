import re
from time import perf_counter

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


is_valid_keybind_re = re.compile("^<(F[1-9]|(1[0-2]))|(Control-[a-zA-Z0-9])>$")


def validate_keybind_or_default(keybind, default):

    match = is_valid_keybind_re.match(keybind)

    return default if match is None else keybind


a = perf_counter()

for test in tests:
    validate_keybind_or_default(test, "something")

print(perf_counter() - a)
