"""Collections of various bits of code that should not be included during compilation"""

import platform
import re
from collections import defaultdict

from compile_utils.regex import RegexReplacement
from turbojpeg import DEFAULT_LIB_PATHS as turbojpeg_platforms

_skip_functions_kwargs: dict[str, set[str]] = {
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
        "fromqimage",
        "fromqpixmap",
        "getexif",
        "preinit",
        "effect_mandelbrot",
        "get_child_images",
        "load_from_fp",
        "show",
        "toqimage",
        "toqpixmap",
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

_skip_function_calls_kwargs: dict[str, set[str]] = {"PIL.TiffTags": {"_populate"}}

_skip_vars_kwargs: dict[str, set[str]] = {
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

_skip_classes_kwargs: dict[str, set[str]] = {
    "PIL.Image": {"DecompressionBombWarning"},
    "PIL.ImageFile": {"_Tile"},
}

_noop_functions_kwargs: dict[str, set[str]] = {
    "PIL._deprecate": {"deprecate"},
}

_skip_dict_keys_kwargs: dict[str, set[str]] = {
    "turbojpeg": {k for k in turbojpeg_platforms if k != platform.system()}.union(
        {"Windows"}
    )
}


dict_keys_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_dict_keys_kwargs
)
functions_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_functions_kwargs
)
function_calls_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_function_calls_kwargs
)
functions_to_noop: defaultdict[str, set[str]] = defaultdict(
    set, **_noop_functions_kwargs
)
vars_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_vars_kwargs)
classes_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_classes_kwargs)

regex_to_apply: dict[str, set[RegexReplacement]] = {
    "PIL.Image": {
        RegexReplacement(
            pattern="""try:
    from defusedxml import ElementTree
except ImportError:
    ElementTree = None""",
            replacement="",
        ),
        RegexReplacement(
            pattern="""try:
    import cffi
except ImportError:
    cffi = None""",
            replacement="cffi = None",
        ),
    },
    "send2trash.__init__": {
        RegexReplacement(pattern=".*", replacement="", flags=re.DOTALL)
    },
    "send2trash.win.__init__": {
        RegexReplacement(pattern=".*", replacement="", flags=re.DOTALL)
    },
    # Fix issue with autoflake
    "send2trash.compat": {
        RegexReplacement(
            pattern="""
try:
    from collections.abc import Iterable as iterable_type
except ImportError:
    from collections import Iterable as iterable_type.*""",
            replacement="""
from collections.abc import Iterable
iterable_type = Iterable""",
        )
    },
    # We don't use pathlib's Path, remove support for it
    "send2trash.util": {
        RegexReplacement(
            pattern=r""".*\[path\.__fspath__\(\).*\]""",
            replacement="",
        )
    },
}
