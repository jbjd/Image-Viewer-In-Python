import os
from typing import Final

from PIL.Image import Image, Resampling, fromarray
from turbojpeg import TJPF_RGB, TurboJPEG

from util.PIL import resize


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    __slots__ = ("jpeg_helper", "screen_height", "screen_width")

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: Final[int] = screen_width
        self.screen_height: Final[int] = screen_height

        turbo_jpeg_lib_path: str | None = None  # None will auto detect

        if os.name == "nt":
            import platform

            suffix: str = "_x86" if platform.architecture()[0] == "32bit" else ""
            turbo_jpeg_lib_path = os.path.join(
                path_to_exe,
                f"dll/libturbojpeg{suffix}.dll",
            )

            del platform

        self.jpeg_helper = TurboJPEG(turbo_jpeg_lib_path)

    def get_zoomed_image(self, image: Image, zoom_level: int) -> tuple[Image, bool]:
        """Resizes image using the provided zoom_level and bool if max zoom reached.

        Raises ValueError if image exceeds JPEG limit of 65,535 pixels in any dimension
        """
        width, height = image.size
        zoom_factor: float = self._calc_zoom_factor(width, height, zoom_level)

        dimensions, interpolation = self.dimension_finder(
            *self._scale_dimensions(image.size, zoom_factor)
        )
        dimensions = self._scale_dimensions(dimensions, zoom_factor)

        # TODO: Refactor handling of hitting JPEG limit of 65,535
        if dimensions[0] > 65_535 or dimensions[1] > 65_535:
            raise ValueError

        max_zoom_hit: bool = self._too_zoomed_in(dimensions)
        if max_zoom_hit:
            if dimensions[1] < self.screen_height:
                dimensions = self._fit_to_screen_height(width, height)
            elif dimensions[0] < self.screen_width:
                dimensions = self._fit_to_screen_width(width, height)

        return resize(image, dimensions, interpolation), max_zoom_hit

    def _calc_zoom_factor(self, width: int, height: int, zoom_level: int) -> float:
        """Calcs zoom factor based on zoom level and w/h ratio"""
        # w/h ratio divide by magic 6 since seemed best after testing
        wh_ratio: int = 1 + max(width // height, height // width) // 6
        return (1.4**zoom_level) * wh_ratio

    # TODO: ZOOM_MIN could be inherent within the dimension check
    # Check for if dimensions are both 2x larger than screen
    # This will also allow for all images to be zoomed at least 2x
    def _too_zoomed_in(self, dimensions: tuple[int, int]) -> bool:
        """Returns bool if new image dimensions would zoom in too much"""
        return (
            dimensions[0] / 2 >= self.screen_width
            and dimensions[1] / 2 >= self.screen_height
        )

    @staticmethod
    def _scale_dimensions(t: tuple[int, int], scale: float) -> tuple[int, int]:
        first, second = t
        return (int(first * scale), int(second * scale))

    def _get_jpeg_scale_factor(
        self, image_width: int, image_height: int
    ) -> tuple[int, int] | None:
        """Gets Turbo JPEG scaling factor for images larger than screen"""
        ratio_to_screen: float = max(
            image_width / self.screen_width, image_height / self.screen_height
        )

        if ratio_to_screen >= 4:
            return (1, 4)
        if ratio_to_screen >= 2:
            return (1, 2)
        return None

    def _get_jpeg_fit_to_screen(self, image: Image) -> Image:
        """Resizes a JPEG utilizing libjpeg-turbo to shrink very large images"""
        image_width, image_height = image.size
        scale_factor: tuple[int, int] | None = self._get_jpeg_scale_factor(
            image_width, image_height
        )
        # if small do a normal resize, otherwise utilize libJpegTurbo
        if scale_factor is None:
            return self._fit_to_screen(image)

        image.fp.seek(0)  # type: ignore
        image_as_array = self.jpeg_helper.decode(
            image.fp.read(),  # type: ignore
            TJPF_RGB,
            scale_factor,
            0,
        )
        return self._fit_to_screen(fromarray(image_as_array))

    def _fit_to_screen(self, image: Image) -> Image:
        """Resizes image to screen with PIL"""
        return resize(image, *self.dimension_finder(*image.size))

    def get_image_fit_to_screen(self, image: Image) -> Image:
        """Resizes image to screen using either libjpeg-turbo or PIL"""
        if image.format == "JPEG":
            return self._get_jpeg_fit_to_screen(image)

        return self._fit_to_screen(image)

    def dimension_finder(
        self, image_width: int, image_height: int
    ) -> tuple[tuple[int, int], Resampling]:
        """Fits dimensions to height if width within screen,
        else fit to width and let height go off screen.
        Returns new width/height, and interpolation to use"""
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
        if height_is_big or width_is_big:
            return Resampling.BICUBIC

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
