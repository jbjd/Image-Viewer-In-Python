# -*- coding:utf-8 -*-

"""
Created By    : Bongdang
"""

from __future__ import annotations
from .enums import BlockType, ExtensionLabel, get_enum
from struct import unpack, calcsize
from typing import BinaryIO, Union


def read_struct_or_int(bytes: bytes, fmt: str) -> Union[tuple, int]:
    try:
        read_size = calcsize(fmt)
        if len(bytes) == read_size:
            ret = unpack(fmt, bytes)
            if type(ret) is int and len(ret) == 1:
                ret = ret[0]
        else:
            raise Exception("invalid struct size")
    except Exception as e:
        print(e)
        ret = None

    return ret


class Header:
    __slots__ = ["magic", "version"]

    @classmethod
    def size(cls) -> int:
        return 6

    def __init__(self, bytes: bytes) -> None:
        # print(bytes)
        self.magic = [0, 0, 0]
        unpacked_t = read_struct_or_int(bytes, "<3B3s")
        self.magic, self.version = unpacked_t[:3], unpacked_t[-1]
        if not self.magic == (0x47, 0x49, 0x46):  # check 'GIF'
            raise Exception("Not GIF magic header")

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        for x in self.magic:
            barr.append(x)
        for x in self.version:
            barr.append(x)
        fp.write(barr)


class LogicalScreenDescriptor:
    __slots__ = [
        "screen_width",
        "screen_height",
        "flags",
        "bg_color_index",
        "pixel_aspect_ratio",
        "is_color_table",
        "color_table_size_v",
    ]

    @classmethod
    def size(cls) -> int:
        return 7

    def __init__(self, bytes: bytes) -> None:
        unpacked_t = read_struct_or_int(bytes, "<HHBBB")
        (
            self.screen_width,
            self.screen_height,
            self.flags,
            self.bg_color_index,
            self.pixel_aspect_ratio,
        ) = unpacked_t

        self.is_color_table = None
        self.color_table_size_v = None

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.screen_width & 0xFF)
        barr.append((self.screen_width & 0xFF00) >> 8)
        barr.append(self.screen_height & 0xFF)
        barr.append((self.screen_height & 0xFF00) >> 8)
        barr.append(self.flags)
        barr.append(self.bg_color_index)
        barr.append(self.pixel_aspect_ratio)
        fp.write(barr)

    @property
    def has_color_table(self) -> bool:
        if self.is_color_table:
            return self.is_color_table
        self.is_color_table = (self.flags & 0x80) != 0
        return self.is_color_table

    @property
    def color_table_size(self) -> int:
        if self.color_table_size_v:
            return self.color_table_size_v
        self.color_table_size_v = 2 << (self.flags & 0x07)
        return self.color_table_size_v


class ColorTable:
    class ColorTableEntry:
        __slots__ = ["red", "green", "blue"]

        def __init__(self, r: int, g: int, b: int) -> None:
            self.red, self.green, self.blue = r, g, b

        def write(self, fp: BinaryIO) -> None:
            barr = bytearray()
            barr.append(self.red)
            barr.append(self.green)
            barr.append(self.blue)
            fp.write(barr)

    __slots__ = ["entries"]

    def __init__(self, bytes: bytes) -> None:
        self.entries = []
        len_bytes = len(bytes) // 3
        color_gen = (bytes[i * 3 : i * 3 + 3] for i in range(len_bytes))
        for pixel in color_gen:
            self.entries.append(ColorTable.ColorTableEntry(*pixel))

    def write(self, fp: BinaryIO) -> None:
        for blk in self.entries:
            blk.write(fp)


class Block:
    __slots__ = ["block_value", "block_type", "body"]

    def __init__(self, byte: int) -> None:
        self.block_value = byte
        self.block_type = get_enum(BlockType, self.block_value)
        self.body = None

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.block_value)
        fp.write(barr)
        if self.block_type and self.body is not None:
            self.body.write(fp)

    @property
    def is_extention_block(self) -> bool:
        if self.body is not None:
            return self.block_type == BlockType.EXTENTION
        return False

    @property
    def is_image_desc_block(self) -> bool:
        if self.body is not None:
            return self.block_type == BlockType.IMAGE_DESC
        return False

    @property
    def get_extention(self) -> Extension:
        if self.body is not None:
            return self.body
        return None

    @property
    def get_image_body(self) -> ImageData:
        if self.body is not None:
            return self.body
        return None


class LocalImageDescriptor:
    __slots__ = [
        "left",
        "top",
        "width",
        "height",
        "flags",
        "local_color_table",
        "image_data",
        "is_local_color_table",
        "local_color_table_size",
        "is_interlaced",
        "is_sorted_color",
    ]

    @classmethod
    def size(cls) -> int:
        return 9

    def __init__(self, bytes: bytes) -> None:
        unpacked_t = read_struct_or_int(bytes, "<HHHHB")
        self.left, self.top, self.width, self.height, self.flags = unpacked_t
        self.is_local_color_table = None
        self.local_color_table_size = None
        self.is_interlaced = None
        self.is_sorted_color = None
        self.image_data = None

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.left & 0xFF)
        barr.append((self.left & 0xFF00) >> 8)
        barr.append(self.top & 0xFF)
        barr.append((self.top & 0xFF00) >> 8)
        barr.append(self.width & 0xFF)
        barr.append((self.width & 0xFF00) >> 8)
        barr.append(self.height & 0xFF)
        barr.append((self.height & 0xFF00) >> 8)
        barr.append(self.flags)
        fp.write(barr)
        if self.has_color_table:
            self.local_color_table.write(fp)
        self.image_data.write(fp)

    @property
    def has_color_table(self) -> bool:
        if self.is_local_color_table:
            return self.is_local_color_table
        self.is_local_color_table = (self.flags & 0x80) != 0
        return self.is_local_color_table

    @property
    def has_interlace(self) -> bool:
        if self.is_interlaced:
            return self.is_interlaced
        self.is_interlaced = (self.flags & 0x40) != 0
        return self.is_interlaced

    @property
    def has_sorted_color_table(self) -> bool:
        if self.is_sorted_color:
            return self.is_sorted_color
        self.is_sorted_color = (self.flags & 0x20) != 0
        return self.is_sorted_color

    @property
    def color_table_size(self) -> int:
        if self.local_color_table_size:
            return self.local_color_table_size
        self.local_color_table_size = 2 << (self.flags & 7)
        return self.local_color_table_size


class Extension:
    __slots__ = ["label_value", "label", "extbody"]

    def __init__(self, byte: int) -> None:
        self.label_value = byte
        self.label = get_enum(ExtensionLabel, self.label_value)
        self.extbody = None

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.label_value)
        fp.write(barr)
        self.extbody.write(fp)

    @property
    def is_graphic_control(self) -> bool:
        if self.extbody is not None:
            return self.label == ExtensionLabel.GRAPHIC_CONTROL
        return False

    @property
    def get_graphic_control(self) -> ExtGraphicControl:
        if self.extbody is not None:
            return self.extbody
        return None


class ExtGraphicControl:
    __slots__ = [
        "block_size",
        "flags",
        "delay_time",
        "transparent_idx",
        "terminator",
        "transparent_color_flag_v",
        "user_input",
    ]

    @classmethod
    def size(cls) -> int:
        return 6

    def __init__(self, bytes: bytes) -> None:
        # print(bytes)
        unpacked_t = read_struct_or_int(bytes, "<BBHBB")
        (
            self.block_size,
            self.flags,
            self.delay_time,
            self.transparent_idx,
            self.terminator,
        ) = unpacked_t
        if not self.block_size == 0x04:
            raise Exception("Wrong Graphic control block size")
        self.transparent_color_flag_v = None
        self.user_input = None
        if not self.terminator == 0x00:
            raise Exception("BAD Graphic control terminator")

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.block_size)
        barr.append(self.flags)
        barr.append(self.delay_time & 0xFF)
        barr.append((self.delay_time & 0xFF00) >> 8)
        barr.append(self.transparent_idx)
        barr.append(self.terminator)
        fp.write(barr)

    @property
    def transparent_color_flag(self) -> bool:
        if self.transparent_color_flag_v:
            return self.transparent_color_flag_v
        self.transparent_color_flag_v = (self.flags & 1) != 0
        return self.transparent_color_flag_v

    @property
    def user_input_flag(self) -> bool:
        if self.user_input:
            return self.user_input
        self.user_input = (self.flags & 2) != 0
        return self.user_input


class ExtApplication:
    __slots__ = [
        "len_bytes",
        "application_identifier",
        "application_auth_code",
        "app_info",
        "is_XMP",
    ]

    @classmethod
    def size(cls) -> int:
        return 11

    def __init__(self, bytes: bytes) -> None:
        data_size = len(bytes)
        # print(data_size)
        if data_size == 16:
            self.is_XMP = False
        else:
            self.is_XMP = True
        unpack_t = read_struct_or_int(bytes, f"<B8s3B{data_size - 12}B")
        self.len_bytes = unpack_t[0]
        self.application_identifier = unpack_t[1]
        self.application_auth_code = unpack_t[2:5]
        self.app_info = unpack_t[5:]
        if not self.len_bytes == 11:
            # print(self.len_bytes)
            raise Exception("Wrong Applicaion ID block length")
        # if self.is_XMP:
        #    print(len(self.app_info))
        #    print(self.app_info[-5:])

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.len_bytes)
        for x in self.application_identifier:
            barr.append(x)
        for x in self.application_auth_code:
            barr.append(x)
        for x in self.app_info:
            barr.append(x)
        fp.write(barr)


class ImageData:
    __slots__ = ["lzw_min_code_size", "subblocks"]

    def __init__(self, byte: int) -> None:
        self.lzw_min_code_size = byte
        self.subblocks = None

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.lzw_min_code_size[0])
        fp.write(barr)
        for subs in self.subblocks:
            subs.write(fp)


class Subblock:
    __slots__ = ["len_bytes", "bytes"]

    def __init__(self, bytes: bytes) -> None:
        self.len_bytes = bytes[0]
        self.bytes = bytes[1:]

    def write(self, fp: BinaryIO) -> None:
        barr = bytearray()
        barr.append(self.len_bytes)
        for x in self.bytes:
            barr.append(x)
        fp.write(barr)


class CommonSubblocks:
    __slots__ = ["subblocks"]

    def __init__(self) -> None:
        self.subblocks = None

    def write(self, fp: BinaryIO) -> None:
        for subs in self.subblocks:
            subs.write(fp)
