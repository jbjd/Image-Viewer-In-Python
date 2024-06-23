"""Collections of various bits of code that should not be included during compilation"""

from collections import defaultdict

_function_kwargs: dict[str, set[str]] = {
    "turbojpeg": {
        "crop_multiple",
        "scale_with_quality",
        "encode_from_yuv",
        "decode_to_yuv",
        "decode_to_yuv_planes",
        "__map_luminance_to_dc_dct_coefficient",
        "__get_dc_dqt_element",
    },
    "PIL.ImageFont": {"__getstate__", "__setstate__"},
    "PIL.Image": {
        "__getstate__",
        "__setstate__",
        "_getxmp",
        "_repr_image",
        "_repr_jpeg_",
        "_repr_pretty_",
        "_repr_png_",
        "_show",
        "getexif",
        "preinit",
        "effect_mandelbrot",
        "get_child_images",
        "load_from_fp",
        "show",
    },
    "PIL.ImageDraw": {"getdraw"},
    "PIL.ImageFile": {"verify", "raise_oserror"},
    "PIL.ImageTk": {"_show"},
    "PIL.GifImagePlugin": {"_save_netpbm", "getheader", "getdata"},
    "PIL.JpegImagePlugin": {"getxmp", "_getexif", "_save_cjpeg", "load_djpeg"},
    "PIL.PngImagePlugin": {"getxmp"},
    "PIL.WebPImagePlugin": {"getxmp"},
    "PIL.TiffTags": {"_populate"},
}

_function_call_kwargs: dict[str, set[str]] = {"PIL.TiffTags": {"_populate"}}

_vars_kwargs: dict[str, set[str]] = {
    "turbojpeg": {
        "TJERR_FATAL",
        "TJCS_CMYK",
        "TJPF_BGRX",
        "TJPF_BGRA",
        "TJPF_ABGR",
        "TJPF_ARGB",
        "TJFLAG_LIMITSCANS",
    },
    "PIL.GifImagePlugin": {"format_description"},
    "PIL.JpegImagePlugin": {"format_description"},
    "PIL.PngImagePlugin": {"format_description"},
    "PIL.WebPImagePlugin": {"format_description"},
}

_classes_kwargs: dict[str, set[str]] = {
    "PIL.ImageFile": {"_Tile"},
}

functions_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_function_kwargs)
function_calls_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_function_call_kwargs
)
vars_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_vars_kwargs)
classes_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_classes_kwargs)

regex_to_apply: dict[str, set[tuple[str, str]]] = {
    "send2trash.compat": {
        (
            ".+",
            """
import os
text_type = str
binary_type = bytes
if os.supports_bytes_environ:
    environb = os.environb
from collections.abc import Iterable as iterable_type""",
        )
    },
}

modules_to_not_autoflake: set[str] = {"send2trash.compat"}
