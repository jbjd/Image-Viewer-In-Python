from PIL.ImageTk import PhotoImage


# struct for holding cached images
# for some reason this stores less data than a regular tuple based on my tests
class CachedImage:
    __slots__ = ("width", "height", "size_as_text", "image", "bit_size")

    def __init__(self, width, height, size_as_text, image, bit_size) -> None:
        self.width: int = width
        self.height: int = height
        self.size_as_text: str = size_as_text
        self.image: PhotoImage = image
        self.bit_size: int = bit_size


class ImagePath:
    __slots__ = ("suffix", "name")

    def __init__(self, name: str) -> None:
        self.suffix = name[name.rfind(".") :].lower()
        self.name = name
