# -*- coding:utf-8 -*-

"""
Created By    : Bongdang
"""

from __future__ import annotations

DESCRIPTION: str = "GIF raw reading Library"
VERSION: str = "0.1.0"
AUTHOR: str = "bongdang"
from .enums import BlockType, ExtensionLabel
from .subclasses import (
    Header,
    LogicalScreenDescriptor,
    ColorTable,
    Block,
    LocalImageDescriptor,
    Extension,
    ExtGraphicControl,
    ExtApplication,
    ImageData,
    Subblock,
    CommonSubblocks,
)
from typing import Generator, Union
from io import BytesIO


class GifRaw:
    class StructRead:
        """
        Currently, Always read whole file. you must have enough memory!
        """

        def __init__(self, fname: str) -> None:
            try:
                with open(fname, "rb") as rf:
                    self.data = rf.read()
                self.data_len = len(self.data)
                self.cur_point = 0
            except:
                raise Exception(f"can't open/read file({fname})")

        def read_byte(self) -> int:
            ret = self.data[self.cur_point]
            self.data_len -= 1
            self.cur_point += 1
            return ret

        def read_bytes(self, len: int) -> bytes:
            chunk = self.data[self.cur_point : self.cur_point + len]
            self.data_len -= len
            self.cur_point += len
            return chunk

        def peek_byte(self, offset: int = 0) -> int:
            return self.data[self.cur_point + offset]

    __slots__ = [
        "hdr",
        "logical_screen_desc",
        "global_color_table",
        "blocks",
        "frames",
        "raw_img_list",
        "reader",
        "is_valid_gif",
    ]

    def __repr__(self) -> str:
        return f"{DESCRIPTION} : Version ({VERSION}) : by {AUTHOR}"

    def __init__(self, gif_file: str) -> None:
        """
        GifRaw Main Class init routine.
        """
        self.hdr = None
        self.logical_screen_desc = None
        self.global_color_table = None
        self.blocks = None
        self.frames = 0
        self.raw_img_list = None

        self.reader = GifRaw.StructRead(gif_file)
        self.is_valid_gif = self.read_all_sections()

    def handle_each_section(self) -> Generator[bytes, Union[bool, int], None]:
        """
        This member function is for yield each chunk for GIF process.
        Some routines receives form coroutine.send() for conditional jobs.
        chunks divided like bellow.
            Header parts
                header
                logical screen description
                color table if any
            Blocks parts ( loop until GIF EOF Mark )
                block type ( 1 byte )
                if image
                    image description
                    if local color table
                        local color table
                    image chunks
                else if extention
                    extention type ( 1 byte )
                    if application id
                        application id chunk
                    else if graphic control
                        graphic control chunk
                    else if comment
                        comment chunk
                else if EOF
                    // END

        """

        def sub_chunk_yielding() -> Generator[bytes, bool, None]:
            is_left = True
            while is_left:
                chunk_size = self.reader.peek_byte()
                is_left = yield self.reader.read_bytes(chunk_size + 1)
            # dummy yield for next request!!! -- bongdang
            yield

        def header_part_yielding() -> Generator[bytes, None, None]:
            # first header
            yield self.reader.read_bytes(Header.size())
            # seconf LogicalScreenDescriptor
            yield self.reader.read_bytes(LogicalScreenDescriptor.size())

            if self.logical_screen_desc.has_color_table:
                yield self.reader.read_bytes(
                    self.logical_screen_desc.color_table_size * 3
                )

        def image_descriptor_yielding() -> Generator[bytes, int, None]:
            color_table_size = yield self.reader.read_bytes(LocalImageDescriptor.size())
            # if has color table
            if color_table_size != 0:
                yield self.reader.read_bytes(color_table_size * 3)
            # and image data
            # first LZW_min_code_size
            yield self.reader.read_bytes(1)
            # iterate subblocks
            yield from sub_chunk_yielding()

        def extention_yielding() -> Generator[bytes, None, None]:
            # check ext type
            ext_type = self.reader.read_byte()
            yield ext_type
            if ext_type == ExtensionLabel.APPLICATION.value:
                n_exeapp_size = ExtApplication.size()
                chunk_add_size = self.reader.peek_byte(offset=n_exeapp_size + 1)
                if self.reader.peek_byte(offset=n_exeapp_size + chunk_add_size) != 0:
                    # if first byte is not 0, maybe XMP case -BAD spec. - bongdang
                    chunk_add_size = 1
                    while (
                        self.reader.peek_byte(offset=n_exeapp_size + chunk_add_size)
                        != 0x00
                    ):
                        chunk_add_size += 1
                    chunk_add_size += 1  # 1 for terminator
                else:
                    chunk_add_size += 2  # 1 for size, 1 for terminator
                yield self.reader.read_bytes(n_exeapp_size + chunk_add_size)
            elif ext_type == ExtensionLabel.GRAPHIC_CONTROL.value:
                yield self.reader.read_bytes(ExtGraphicControl.size())
            elif ext_type == ExtensionLabel.COMMENT.value:
                yield from sub_chunk_yielding()
            else:
                yield from sub_chunk_yielding()

        # start!
        yield from header_part_yielding()

        while True:
            try:
                block_data = self.reader.read_byte()
                if block_data is None:
                    # maybe wrong file, then Stop Iteration
                    raise Exception(f"Wrong Block Data {block_data}")
                yield block_data
                if block_data == BlockType.IMAGE_DESC.value:
                    yield from image_descriptor_yielding()
                elif block_data == BlockType.EXTENTION.value:
                    yield from extention_yielding()
                if block_data == BlockType.EOF.value:
                    # will cause StopIteration! - bongdang
                    return
            except:
                return

    def read_all_sections(self) -> bool:
        def read_sub_blocks(gen: Generator[bytes, bool, None], body) -> None:
            body.subblocks = []
            sub_blk_data = next(gen)
            is_left = True
            while is_left:
                sub_blk_cls = Subblock(sub_blk_data)
                body.subblocks.append(sub_blk_cls)
                if sub_blk_cls.len_bytes == 0:
                    is_left = False
                sub_blk_data = gen.send(is_left)

        def read_image_descriptor(gen: Generator[bytes, int, None], blk: Block) -> None:
            blk.body = LocalImageDescriptor(next(gen))
            if blk.body.has_color_table:
                c_tbl_data = gen.send(blk.body.color_table_size)
                blk.body.local_color_table = ColorTable(c_tbl_data)
                img_data = next(gen)
            else:
                img_data = gen.send(0)
            blk.body.image_data = ImageData(img_data)
            read_sub_blocks(gen, blk.body.image_data)

        def read_extention_block(gen: Generator[bytes, None, None], blk: Block) -> None:
            ext_type = next(gen)
            blk.body = Extension(ext_type)
            if ext_type == ExtensionLabel.APPLICATION.value:
                blk.body.extbody = ExtApplication(next(gen))
            elif ext_type == ExtensionLabel.GRAPHIC_CONTROL.value:
                blk.body.extbody = ExtGraphicControl(next(gen))
            elif ext_type == ExtensionLabel.COMMENT.value:
                blk.body.extbody = CommonSubblocks()
                read_sub_blocks(gen, blk.body.extbody)
            else:
                blk.body.extbody = CommonSubblocks()
                read_sub_blocks(gen, blk.body.extbody)

        # start with get Generator
        gen = self.handle_each_section()

        try:
            # first header
            self.hdr = Header(next(gen))
            # second LSD
            self.logical_screen_desc = LogicalScreenDescriptor(next(gen))
            if self.logical_screen_desc.has_color_table:
                self.global_color_table = ColorTable(next(gen))

            self.blocks = []
            self.frames = 0
            while True:
                try:
                    block_data = next(gen)
                    blk = Block(block_data)
                    if block_data == BlockType.IMAGE_DESC.value:
                        read_image_descriptor(gen, blk)
                        self.frames += 1
                    elif block_data == BlockType.EXTENTION.value:
                        read_extention_block(gen, blk)

                    self.blocks.append(blk)
                    if blk.block_type == BlockType.EOF.value:
                        return True
                except StopIteration:
                    break
            return True
        except Exception as e:
            return False

    def make_raw_image_list(self) -> None:
        """
        This Function make each single frame as valid GIF file contents.
        hdr, logical_screen_desc, global_color_table(if any),GRAPHIC_CONTROL Block, IMAGE_DESC Block, GIF_END
        If write to file each buffer, it will be displayable GIF file.
        """

        saved_block_idx = 0
        self.raw_img_list = []
        for frameno in range(self.frames):
            memio = BytesIO()
            is_one_file = False

            # make header
            self.hdr.write(memio)
            self.logical_screen_desc.write(memio)
            if self.logical_screen_desc.has_color_table:
                self.global_color_table.write(memio)
            cur_block_idx = 0

            # make blocks
            for block in self.blocks:
                cur_block_idx += 1
                if cur_block_idx <= saved_block_idx:
                    continue
                elif block.is_image_desc_block:
                    frameno += 1
                    is_one_file = True
                    saved_block_idx = cur_block_idx

                block.write(memio)
                if is_one_file:
                    self.blocks[-1].write(memio)
                    break

            # add list for later
            self.raw_img_list.append(memio.getbuffer())
        return None
