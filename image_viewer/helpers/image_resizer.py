import os
from typing import Final

from PIL.Image import Image, Resampling, fromarray
from turbojpeg import TJPF_RGB, TurboJPEG


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    __slots__ = "jpeg_helper", "screen_height", "screen_width"

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: Final[int] = screen_width
        self.screen_height: Final[int] = screen_height

        self.jpeg_helper = TurboJPEG(
            os.path.join(path_to_exe, "dll/libturbojpeg.dll")
            if os.name == "nt"
            else None
        )

    def get_zoomed_image(self, image: Image, zoom_scale: float) -> Image:
        """Resizes image using the provided zoom_level and bool if max zoom reached"""
        dimensions, interpolation = self.dimension_finder(
            *self._scale_dimensions(image.size, zoom_scale)
        )
        dimensions = self._scale_dimensions(dimensions, zoom_scale)

        return image.resize(dimensions, interpolation)

    @staticmethod
    def _scale_dimensions(t: tuple[int, int], scale: float) -> tuple[int, int]:
        first, second = t
        return (int(first * scale), int(second * scale))

    def _get_jpeg_pyramid(self, image: Image) -> list[Image]:
        """Returns list of the same jpeg in desending sizes using JpegTurbo
        where last image is exactly fit to screen"""
        width: int
        height: int
        width, height = image.size
        jpeg_scale: int = 1

        image.fp.seek(0)  # type: ignore
        image_buffer = image.fp.read()  # type: ignore
        pyramid: list[Image] = [image.copy()]

        while width > (self.screen_width << 1) or height > (self.screen_width << 1):
            width >>= 1
            height >>= 1
            jpeg_scale <<= 1
            if jpeg_scale <= 8:
                scale: tuple[int, int] = (1, jpeg_scale)
                image_as_array = self.jpeg_helper.decode(
                    image_buffer, TJPF_RGB, scale, 0
                )
                pyramid.append(fromarray(image_as_array))
            else:
                pyramid.append(pyramid[-1].resize((width, height), Resampling.HAMMING))

        pyramid.append(self._fit_to_screen(pyramid[-1]))

        return pyramid

    def _fit_to_screen(self, image: Image) -> Image:
        """Resizes image to screen and returns it as a PhotoImage"""
        size, resample = self.dimension_finder(*image.size)
        return image.resize(size, resample)

    def get_image_pyramid(self, image: Image) -> list[Image]:
        """Returns list of the same image in desending sizes
        where last image is exactly fit to screen"""
        width: int
        height: int
        width, height = image.size
        frame_count: int = getattr(image, "n_frames", 1)

        if (
            width <= self.screen_width and height <= self.screen_height
        ) or frame_count > 1:
            return [self._fit_to_screen(image)]

        if image.format == "JPEG":
            return self._get_jpeg_pyramid(image)

        pyramid: list[Image] = [image.copy()]

        while width > (self.screen_width << 1) or height > (self.screen_height << 1):
            width >>= 1
            height >>= 1
            pyramid.append(pyramid[-1].resize((width, height), Resampling.HAMMING))

        pyramid.append(self._fit_to_screen(pyramid[-1]))

        return pyramid

    def dimension_finder(
        self, image_width: int, image_height: int
    ) -> tuple[tuple[int, int], Resampling]:
        """Fits dimensions to height if width within screen,
        else fit to width and let height go off screen.
        Returns new width, new height, and interpolation to use"""
        interpolation: Resampling = self._determine_interpolation(
            image_width, image_height
        )
        fit_to_height: tuple[int, int] = self._fit_to_screen_height(
            image_width, image_height
        )
        return (
            fit_to_height
            if fit_to_height[0] <= self.screen_width
            else self._fit_to_screen_width(image_width, image_height)
        ), interpolation

    def _determine_interpolation(
        self, image_width: int, image_height: int
    ) -> Resampling:
        """Determine resampling to use based on image and screen"""
        height_is_big: bool = image_height >= self.screen_height
        width_is_big: bool = image_width >= self.screen_width

        if height_is_big and width_is_big:
            return Resampling.HAMMING
        elif height_is_big or width_is_big:
            return Resampling.BICUBIC
        else:
            return Resampling.LANCZOS

    def _fit_to_screen_height(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's height"""
        width: int = round(image_width * (self.screen_height / image_height))
        return (width, self.screen_height)

    def _fit_to_screen_width(
        self, image_width: int, image_height: int
    ) -> tuple[int, int]:
        """Fits dimensions to screen's width"""
        height: int = round(image_height * (self.screen_width / image_width))
        return (self.screen_width, height)
