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
        "_apply_env_variables",
        "_repr_image",
        "_repr_jpeg_",
        "_repr_pretty_",
        "_repr_png_",
        "_show",
        "_wedge",
        "fromqimage",
        "fromqpixmap",
        "getexif",
        "getxmp",
        "preinit",
        "effect_mandelbrot",
        "get_child_images",
        "load_from_fp",
        "register_mime",
        "show",
        "toqimage",
        "toqpixmap",
    },
    "PIL.ImageDraw": {"_color_diff", "getdraw", "floodfill"},
    "PIL.ImageFile": {"get_format_mimetype", "verify", "raise_oserror"},
    "PIL.ImageTk": {"_pilbitmap_check", "_show"},
    "PIL.GifImagePlugin": {"_save_netpbm", "getheader", "getdata"},
    "PIL.JpegImagePlugin": {"_getexif", "_save_cjpeg", "load_djpeg"},
    "PIL.ImageMath": {"eval", "unsafe_eval"},
    "PIL.TiffTags": {"_populate"},
}

_skip_function_calls_kwargs: dict[str, set[str]] = {
    "PIL.Image": {"_apply_env_variables", "deprecate"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.GifImagePlugin": {"register_mime"},
    "PIL.JpegImagePlugin": {"register_mime"},
    "PIL.PngImagePlugin": {"register_mime"},
    "PIL.WebPImagePlugin": {"register_mime"},
    "PIL.TiffTags": {"_populate"},
}

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
    "PIL.Image": {"USE_CFFI_ACCESS", "MIME"},
    "PIL.ImageTk": {"_pilbitmap_ok"},
    "PIL.GifImagePlugin": {"format_description", "_Palette"},
    "PIL.JpegImagePlugin": {"format_description"},
    "PIL.PngImagePlugin": {"format_description"},
    "PIL.WebPImagePlugin": {"format_description"},
}

_skip_classes_kwargs: dict[str, set[str]] = {
    "PIL.Image": {
        "DecompressionBombWarning",
        "SupportsArrayInterface",
        "SupportsGetData",
    },
    "PIL.ImageFile": {
        "_Tile",
        "Parser",
        "PyCodec",
        "PyCodecState",
        "PyDecoder",
        "PyEncoder",
        "StubHandler",
        "StubImageFile",
    },
    "PIL.ImageTk": {"BitmapImage"},
}

_skip_dict_keys_kwargs: dict[str, set[str]] = {
    "turbojpeg": {k for k in turbojpeg_platforms if k != platform.system()}
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
vars_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_vars_kwargs)
classes_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_classes_kwargs)

regex_to_apply: dict[str, set[RegexReplacement]] = {
    "util.PIL": {RegexReplacement(pattern=r"_Image._plugins = \[\]", replacement="")},
    "PIL.__init__": {
        RegexReplacement(
            pattern=r"_plugins = \[.*?\]", replacement="_plugins = []", flags=re.DOTALL
        )
    },
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
            replacement="",
        ),
        RegexReplacement(pattern="from ._deprecate import deprecate", replacement=""),
        RegexReplacement(
            pattern=r" +if cffi.*?PyAccess.*?return self.pyaccess",
            replacement="",
            flags=re.DOTALL,
        ),
        RegexReplacement(
            pattern=r"def __array_interface__\(self\):.*?return[^\n]*",
            replacement="""def __array_interface__(self):
        new = {}
        new['shape'], new['typestr'] = _conv_type_shape(self)
        return new""",
            flags=re.DOTALL,
        ),
    },
    "PIL.ImageDraw": {
        RegexReplacement(pattern="_Ink =.*", replacement=""),
        RegexReplacement(
            pattern=r"def Draw.*?return ImageDraw.*?\)",
            replacement="""def Draw(im, mode=None): return ImageDraw(im, mode)""",
            flags=re.DOTALL,
        ),
    },
    "PIL.ImageMode": {
        RegexReplacement(
            pattern="from typing import NamedTuple",
            replacement="from collections import namedtuple",
        ),
        RegexReplacement(
            pattern=r"\(NamedTuple\):",
            replacement=r"(namedtuple('ModeDescriptor', ['mode', 'bands', 'basemode', 'basetype', 'typestr'])):",  # noqa E501
        ),
        RegexReplacement(pattern="from ._deprecate import deprecate", replacement=""),
    },
    "PIL.PngImagePlugin": {
        RegexReplacement(pattern=r"raise EOFError\(.*?\)", replacement="raise EOFError")
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
