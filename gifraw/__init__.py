# -*- coding: utf-8 -*-

"""
GIF raw reading Library.

Gifraw is a python GIF reading library.
It is made for adding some feature to PILLOW/imageio palette problem.

by bongdang
"""

DESCRIPTION: str = "GIF raw reading Library"
VERSION: str = "0.1.0"
AUTHOR: str = "bongdang"

from .mainclass import GifRaw

def __repr__():
    return f"{DESCRIPTION} : Version ({VERSION}) : by {AUTHOR}"