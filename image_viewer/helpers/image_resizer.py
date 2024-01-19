import os
from functools import cache

import cv2
from numpy import asarray
from PIL.Image import Image, fromarray
from PIL.ImageTk import PhotoImage
from turbojpeg import TJPF_RGB, TurboJPEG


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.jpeg_helper = TurboJPEG(
            os.path.join(path_to_exe, "dll/libturbojpeg.dll")
            if os.name == "nt"
            else None
        )

    def _array_to_photoimage(
        self, array, image_width: int, image_height: int
    ) -> PhotoImage:
        """Converts and resizes a matrix-like into a PhotoImage fit to the screen"""
        dimensions, interpolation = self.dimension_finder(image_width, image_height)
        return PhotoImage(
            fromarray(cv2.resize(array, dimensions, interpolation=interpolation))
        )

    def _get_jpeg_scale_factor(
        self, image_width: int, image_height: int
    ) -> tuple[int, int] | None:
        """Gets scaling factor for images larger than screen"""
        ratio_to_screen: float = max(
            image_width / self.screen_width, image_height / self.screen_height
        )

        if ratio_to_screen >= 4:
            return (1, 4)
        if ratio_to_screen >= 2:
            return (1, 2)
        return None

    def get_jpeg_fit_to_screen(self, image: Image, path_to_image: str) -> PhotoImage:
        image_width, image_height = image.size
        with open(path_to_image, "rb") as im_bytes:
            image_as_array = self.jpeg_helper.decode(
                im_bytes.read(),
                TJPF_RGB,
                self._get_jpeg_scale_factor(image_width, image_height),
                0,
            )
            return self._array_to_photoimage(image_as_array, image_width, image_height)

    def get_image_fit_to_screen(self, image: Image) -> PhotoImage:
        # cv2 resize is faster than PIL, but convert to RGB then resize is slower
        # PIL resize for non-RGB(A) mode images looks very bad so still use cv2
        return self._array_to_photoimage(
            asarray(
                image if image.mode != "P" else image.convert("RGB"),
                order="C",
            ),
            *image.size,
        )

    @cache
    def dimension_finder(
        self, image_width: int, image_height: int
    ) -> tuple[tuple[int, int], int]:
        """fits dimensions to height if width within screen,
        else fit to width and let height go off screen
        returns: new width, new height, and interpolation to use"""
        interpolation: int = (
            cv2.INTER_AREA
            if image_height > self.screen_height or image_width > self.screen_width
            else cv2.INTER_CUBIC
        )
        width: int = round(image_width * (self.screen_height / image_height))

        return (
            ((width, self.screen_height), interpolation)
            if width <= self.screen_width
            else (
                (
                    self.screen_width,
                    round(image_height * (self.screen_width / image_width)),
                ),
                interpolation,
            )
        )
