"""Collections of various bits of code that should not be included during compilation"""

import os
import platform
import re
from collections import defaultdict

from compile_utils.regex import RegexReplacement
from turbojpeg import DEFAULT_LIB_PATHS as turbojpeg_platforms

_skip_functions_kwargs: dict[str, set[str]] = {
    "numpy._utils.__init__": {"_rename_parameter"},
    "turbojpeg": {
        "__define_cropping_regions",
        "__find_dqt",
        "__get_dc_dqt_element",
        "__map_luminance_to_dc_dct_coefficient",
        "__need_fill_background",
        "crop_multiple",
        "decode_to_yuv",
        "decode_to_yuv_planes",
        "encode_from_yuv",
        "scale_with_quality",
    },
    "PIL.ImageFont": {
        "__getstate__",
        "__setstate__",
        "load_default_imagefont",
        "load_default",
    },
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
    "numpy._core.overrides": {"add_docstring"},
    "PIL.Image": {"_apply_env_variables", "deprecate"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.GifImagePlugin": {"register_mime"},
    "PIL.JpegImagePlugin": {"register_mime"},
    "PIL.PngImagePlugin": {"register_mime"},
    "PIL.WebPImagePlugin": {"register_mime"},
    "PIL.TiffTags": {"_populate"},
}

_skip_vars_kwargs: dict[str, set[str]] = {
    "numpy.version": {"full_version", "git_revision", "release"},
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

remove_all_re = RegexReplacement(pattern=".*", flags=re.DOTALL)
remove_numpy_pytester_re = RegexReplacement(
    pattern=r"\s*from numpy._pytesttester import PytestTester.*?del PytestTester",
    flags=re.DOTALL,
)
regex_to_apply: defaultdict[str, set[RegexReplacement]] = defaultdict(
    set,
    {
        "util.PIL": {RegexReplacement(pattern=r"_Image._plugins = \[\]")},
        "numpy.__init__": {
            RegexReplacement(
                pattern="elif attr == .{0}.:.*?return {0}".format(module),
                flags=re.DOTALL,
            )
            for module in ("fft", "f2py", "typing", "polynomial", "testing", "random")
        }.union(
            {
                remove_numpy_pytester_re,
                RegexReplacement(
                    pattern=r"(el)?if attr == .char.*?return char(\.chararray)?",
                    flags=re.DOTALL,
                ),
                RegexReplacement(  # These are all deprecation warnings
                    pattern=r"if attr in _.*?\)", flags=re.DOTALL
                ),
                RegexReplacement(pattern=r"from \._expired_attrs_2_0 .*"),
                RegexReplacement(
                    pattern=r"def _mac_os_check\(\):.*?del _mac_os_check",
                    flags=re.DOTALL,
                ),
                RegexReplacement(
                    pattern=r"def _sanity_check\(\):.*?del _sanity_check",
                    flags=re.DOTALL,
                ),
            }
        ),
        "numpy._core.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"if not.*raise ImportError\(msg.format\(path\)\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(pattern=r"from \. import _add_newdocs.*"),
            RegexReplacement(
                pattern=r"except ImportError as exc:.*?raise ImportError\(msg\)",
                flags=re.DOTALL,
            ),
        },
        "numpy._core.overrides": {
            RegexReplacement(
                pattern=r"add_docstring\(implementation, dispatcher\.__doc__\)",
                replacement="add_docstring(implementation, '')",
            ),
            RegexReplacement(
                pattern="def set_array_function_like_doc.*?return public_api",
                replacement="def set_array_function_like_doc(a): return a",
                flags=re.DOTALL,
            ),
        },
        "numpy.lib.__init__": {remove_numpy_pytester_re},
        "numpy.linalg.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(pattern=r"from \. import linalg"),
        },
        "numpy.linalg._linalg": {
            RegexReplacement(pattern="from numpy._typing.*"),
        },
        "numpy.ma.__init__": {remove_numpy_pytester_re},
        "numpy.matrixlib.__init__": {remove_numpy_pytester_re},
        "PIL.__init__": {
            RegexReplacement(
                pattern=r"_plugins = \[.*?\]",
                replacement="_plugins = []",
                flags=re.DOTALL,
            )
        },
        "PIL.Image": {
            RegexReplacement(
                pattern="""try:
    from defusedxml import ElementTree
except ImportError:
    ElementTree = None""",
            ),
            RegexReplacement(
                pattern="""try:
    import cffi
except ImportError:
    cffi = None""",
            ),
            RegexReplacement(pattern="from ._deprecate import deprecate"),
            RegexReplacement(
                pattern=r" +if cffi.*?PyAccess.*?return self.pyaccess", flags=re.DOTALL
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
            RegexReplacement(pattern="_Ink =.*"),
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
            RegexReplacement(pattern="from ._deprecate import deprecate"),
        },
        "PIL.PngImagePlugin": {
            RegexReplacement(
                pattern=r"raise EOFError\(.*?\)", replacement="raise EOFError"
            )
        },
        "send2trash.__init__": {remove_all_re},
        "send2trash.win.__init__": {remove_all_re},
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
        "send2trash.util": {RegexReplacement(pattern=r".*\[path\.__fspath__\(\).*\]")},
    },
)
if os.name == "nt":
    regex_to_apply["turbojpeg"].add(
        RegexReplacement(
            pattern=r"if platform.system\(\) == 'Linux'.*return lib_path",
            flags=re.DOTALL,
        )
    )

folders_to_exlcude: list[str] = ["tcl/http1.0", "tcl/tzdata", "tk/images", "tk/msgs"]
# tcl testing and http files are inlucded in dist by nuitka
globs_to_exlucde: list[str] = [
    "tcl*/**/http-*.tm",
    "tcl*/**/tcltest-*.tm",
    "tk/ttk/*Theme.tcl",
    "libcrypto-*",
    "_hashlib.pyd",
    "_lzma.pyd",
    "_bz2.pyd",
]
if os.name == "nt":
    globs_to_exlucde.append("select.pyd")
