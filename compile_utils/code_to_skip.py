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
    },
    "PIL.Image": {
        "_getxmp",
        "getexif",
        "preinit",
        "effect_mandelbrot",
        "get_child_images",
    },
    "PIL.ImageDraw": {"getdraw"},
    "PIL.ImageFile": {"verify", "raise_oserror"},
    "PIL.GifImagePlugin": {"getheader", "getdata"},
    "PIL.JpegImagePlugin": {"getxmp", "_getexif", "_save_cjpeg", "load_djpeg"},
    "PIL.PngImagePlugin": {"getxmp"},
    "PIL.WebPImagePlugin": {"getxmp"},
}

_vars_kwargs: dict[str, set[str]] = {
    "turbojpeg": {
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

functions_to_skip: defaultdict[str, set] = defaultdict(set, **_function_kwargs)
vars_to_skip: defaultdict[str, set] = defaultdict(set, **_vars_kwargs)
classes_to_skip: defaultdict[str, set] = defaultdict(set, **_classes_kwargs)
