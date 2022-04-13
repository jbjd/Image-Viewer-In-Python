# -*- coding:utf-8 -*-

from enum import Enum

def get_enum(enumclass: Enum, value) -> Enum:
    for en in enumclass:
        if en.value == value:
            return en
    return None

class BlockType(Enum):
    EXTENTION = 0x21
    IMAGE_DESC = 0x2C
    EOF = 0x3B

class ExtensionLabel(Enum):
    GRAPHIC_CONTROL = 0xF9
    COMMENT = 0xFE
    APPLICATION = 0xFF