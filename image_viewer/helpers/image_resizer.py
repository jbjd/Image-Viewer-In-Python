import os

from cv2 import INTER_AREA, INTER_CUBIC
from PIL.Image import Image
from PIL.ImageTk import PhotoImage
from turbojpeg import TJPF_RGB, TurboJPEG

from util.array import array_to_photoimage, image_to_array


class ImageResizer:
    """Handles resizing images to fit to the screen"""

    ZOOM_MIN: float = 2.0

    __slots__ = ("jpeg_helper", "screen_height", "screen_width")

    def __init__(self, screen_width: int, screen_height: int, path_to_exe: str) -> None:
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height

        self.jpeg_helper = TurboJPEG(
            os.path.join(path_to_exe, "dll/libturbojpeg.dll")
            if os.name == "nt"
            else None
        )

    def get_zoomed_image(self, image: Image, zoom_factor: float) -> PhotoImage | None:
        """Resizes image using the provided zoom_factor.
        Returns None when max zoom reached"""
        dimensions, interpolation = self.dimension_finder(*image.size)
        dimensions = (
            int(dimensions[0] * zoom_factor),
            int(dimensions[1] * zoom_factor),
        )
        if (
            dimensions[0] > self.screen_width
            and dimensions[1] > self.screen_height
            and zoom_factor > self.ZOOM_MIN
        ):
            return None

        return array_to_photoimage(
            image_to_array(image),
            dimensions,
            interpolation,
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
            return array_to_photoimage(
                image_as_array, *self.dimension_finder(image_width, image_height)
            )

    def get_image_fit_to_screen(self, image: Image, path_to_image: str) -> PhotoImage:
        # cv2 resize is faster than PIL, but convert to RGB then resize is slower
        # PIL resize for non-RGB(A) mode images looks very bad so still use cv2
        if image.format == "JPEG":
            return self.get_jpeg_fit_to_screen(image, path_to_image)

        return array_to_photoimage(
            image_to_array(image),
            *self.dimension_finder(*image.size),
        )

    def dimension_finder(
        self, image_width: int, image_height: int
    ) -> tuple[tuple[int, int], int]:
        """Fits dimensions to height if width within screen,
        else fit to width and let height go off screen
        returns: new width, new height, and interpolation to use"""
        interpolation: int = (
            INTER_AREA
            if image_height > self.screen_height or image_width > self.screen_width
            else INTER_CUBIC
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
