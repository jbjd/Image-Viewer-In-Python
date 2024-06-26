from typing import NamedTuple


class RegexReplacement(NamedTuple):
    pattern: str
    replacement: str
    flags: int = 0