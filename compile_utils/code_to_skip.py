"""Collections of various bits of code that should not be included during compilation"""

import os
import platform
import re
import sys
from collections import defaultdict

from compile_utils.regex import RegexReplacement
from turbojpeg import DEFAULT_LIB_PATHS as turbojpeg_platforms

_skip_functions_kwargs: dict[str, set[str]] = {
    "numpy.__init__": {"__dir__", "_pyinstaller_hooks_dir"},
    "numpy._utils.__init__": {"_rename_parameter"},
    "numpy._core._dtype": {
        "__repr__",
        "__str__",
        "_name_get",
        "_name_includes_bit_suffix",
    },
    "numpy._core.arrayprint": {
        "_array_repr_dispatcher",
        "_array_repr_implementation",
        "_void_scalar_to_string",
        "array_repr",
        "dtype_short_repr",
        "set_string_function",
    },
    "numpy._core.function_base": {
        "_add_docstring",
        "_needs_add_docstring",
        "add_newdoc",
    },
    "numpy._core.getlimits": {"__repr__"},
    "numpy._core.numeric": {"_frombuffer", "_full_dispatcher"},
    "numpy._core.numerictypes": {"maximum_sctype"},
    "numpy._core.overrides": {"verify_matching_signatures"},
    "numpy._core.records": {"__repr__", "__str__"},
    "numpy._core.strings": {
        "_join",
        "_partition",
        "_rpartition",
        "_rsplit",
        "_split",
        "_splitlines",
    },
    "numpy._globals": {"__repr__"},
    "numpy.lib._arraysetops_impl": {"_ediff1d_dispatcher", "ediff1d"},
    "numpy.lib._histograms_impl": {
        "_histogram_bin_edges_dispatcher",
        "histogram_bin_edges",
    },
    "numpy.linalg._linalg": {
        "_convertarray",
        "_cholesky_dispatcher",
        "_qr_dispatcher",
        "_raise_linalgerror_qr",
        "cholesky",
        "qr",
    },
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
    "PIL.Image": {
        "__getstate__",
        "__setstate__",
        "_apply_env_variables",
        "_dump",
        "_repr_image",
        "_repr_jpeg_",
        "_repr_pretty_",
        "_repr_png_",
        "_show",
        "_wedge",
        "alpha_composite",
        "blend",
        "composite",
        "fromqimage",
        "fromqpixmap",
        "getexif",
        "getxmp",
        "preinit",
        "effect_mandelbrot",
        "get_child_images",
        "linear_gradient",
        "load_from_fp",
        "radial_gradient",
        "register_mime",
        "show",
        "toqimage",
        "toqpixmap",
    },
    "PIL.ImageChops": {
        "blend",
        "composite",
        "constant",
        "darker",
        "duplicate",
        "invert",
        "lighter",
        "overlay",
        "soft_light",
        "hard_light",
    },
    "PIL.ImageDraw": {"_color_diff", "getdraw", "floodfill"},
    "PIL.ImageFile": {"get_format_mimetype", "verify", "raise_oserror"},
    "PIL.ImageFont": {
        "__getstate__",
        "__setstate__",
        "load_default_imagefont",
        "load_default",
        "load_path",
    },
    "PIL.ImageOps": {
        "autocontrast",
        "colorize",
        "cover",
        "deform",
        "equalize",
        "exif_transpose",
        "grayscale",
        "mirror",
        "posterize",
        "solarize",
    },
    "PIL.ImagePalette": {"random", "sepia", "wedge"},
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
    "numpy.__init__": {
        "__all__",
        "__array_api_version__",
        "__future_scalars__",
        "__former_attrs__",
        "_int_extended_msg",
        "_msg",
        "_specific_msg",
        "_type_info",
    },
    "numpy._core.arrayprint": {"_default_array_repr"},
    "numpy._core.numerictypes": {"genericTypeRank"},
    "numpy._core.overrides": {"array_function_like_doc", "ArgSpec"},
    "turbojpeg": {
        "__buffer_size_YUV2",
        "__compressFromYUV",
        "__decompressToYUVPlanes",
        "__decompressToYUV2",
        "TJERR_FATAL",
        "TJCS_CMYK",
        "TJPF_ABGR",
        "TJPF_ARGB",
        "TJPF_BGRX",
        "TJPF_BGRA",
        "TJPF_CMYK",
        "TJPF_XBGR",
        "TJFLAG_LIMITSCANS",
        "TJFLAG_STOPONWARNING",
    },
    "PIL.Image": {"USE_CFFI_ACCESS", "MIME"},
    "PIL.ImageTk": {"_pilbitmap_ok"},
    "PIL.GifImagePlugin": {"format_description", "_Palette"},
    "PIL.JpegImagePlugin": {"format_description"},
    "PIL.PngImagePlugin": {"format_description"},
    "PIL.WebPImagePlugin": {"format_description"},
}

_skip_classes_kwargs: dict[str, set[str]] = {
    "numpy._globals": {"_CopyMode"},
    "numpy.exceptions": {
        "ComplexWarning",
        "ModuleDeprecationWarning",
        "RankWarning",
        "TooHardError",
        "VisibleDeprecationWarning",
    },
    "PIL.Image": {"SupportsArrayInterface", "SupportsGetData"},
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
    "PIL.ImageFont": {"TransposedFont"},
    "PIL.ImageOps": {"SupportsGetMesh"},
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
regex_to_apply_py: defaultdict[str, set[RegexReplacement]] = defaultdict(
    set,
    {
        "util.PIL": {RegexReplacement(pattern=r"_Image._plugins = \[\]")},
        "numpy.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"(el)?if attr == .char.*?return char(\.chararray)?",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"elif attr == .(array_api|distutils).:.*?\)", flags=re.DOTALL
            ),
            RegexReplacement(  # These are all deprecation warnings
                pattern=r"if attr in _.*?\)", flags=re.DOTALL
            ),
            RegexReplacement(pattern=r"from \._expired_attrs_2_0 .*"),
            RegexReplacement(
                pattern=r"def (_mac_os_check|_sanity_check)\(.*?del (_mac_os_check|_sanity_check)",  # noqa E501
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"os\.environ\.get\(.NPY_PROMOTION_STATE., .weak.\)",
                replacement="'weak'",
            ),
            RegexReplacement(
                pattern=r"try:\s*__NUMPY_SETUP__.*?__NUMPY_SETUP__ = False",
                replacement="__NUMPY_SETUP__ = False",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"try:\s*?from numpy\.__config__.* from e", flags=re.DOTALL
            ),
            RegexReplacement(pattern=", einsum, einsum_path", count=1),
            RegexReplacement(
                pattern=", (_CopyMode|show_config|histogram_bin_edges|memmap|require)"
            ),
            RegexReplacement(pattern="(ediff1d|array_repr),"),
            RegexReplacement(pattern=r"from \. import matrixlib.*", count=1),
            RegexReplacement(
                pattern=r"from .* import (_distributor_init|(__)?version(__)?)"
            ),
            RegexReplacement(pattern=r"from \.lib import .*"),
            RegexReplacement(
                pattern=r"from \.(lib\.(_arraypad_impl|_npyio_impl|_utils_impl|_polynomial_impl)|matrixlib) import .*?\)",  # noqa E501
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"__numpy_submodules__ =.*?\}", count=1, flags=re.DOTALL
            ),
        }.union(
            {
                RegexReplacement(
                    pattern="elif attr == .{0}.:.*?return {0}".format(module),
                    flags=re.DOTALL,
                )
                for module in (
                    "core",
                    "ctypeslib",
                    "fft",
                    "f2py",
                    "ma",
                    "matlib",
                    "polynomial",
                    "random",
                    "rec",
                    "strings",
                    "testing",
                    "typing",
                )
            }
        ),
        "numpy._core.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"if not.*raise ImportError\(msg.format\(path\)\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \. import (_add_newdocs|_internal|_dtype).*"
            ),
            RegexReplacement(pattern=r"from \.memmap import \*", count=1),
            RegexReplacement(pattern=r"from numpy\.version import .*"),
            RegexReplacement(
                pattern=r"except ImportError as exc:.*?raise ImportError\(msg\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r".*?einsumfunc.*",
            ),
        },
        "numpy._core._methods": {
            RegexReplacement(pattern=r"from numpy\._core import _exceptions", count=1)
        },
        "numpy._core.arrayprint": {RegexReplacement(pattern=", .array_repr.")},
        "numpy._core.numeric": {
            RegexReplacement(pattern=".*_asarray.*", count=3),
        },
        "numpy._core.numerictypes": {
            RegexReplacement(pattern=r"from \._dtype import _kind_name", count=1),
        },
        "numpy._core.overrides": {
            RegexReplacement(
                pattern="def set_array_function_like_doc.*?return public_api",
                replacement="def set_array_function_like_doc(a): return a",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from numpy._core._multiarray_umath import .*?\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \.\._utils\._inspect import getargspec", count=1
            ),
            RegexReplacement(
                pattern="def decorator.*?return public_api",
                replacement="def decorator(i): return i",
                flags=re.DOTALL,
            ),
        },
        "numpy._utils.__init__": {
            RegexReplacement(pattern=r"from \._convertions import .*", count=1)
        },
        "numpy.lib.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"elif attr == .emath.*else:\s*",
                flags=re.DOTALL,
            ),
            RegexReplacement(pattern=r"from \. import _.*"),
            RegexReplacement(pattern=r"from numpy\._core.* import .*"),
            RegexReplacement(pattern=r"from \._version import NumpyVersion"),
            RegexReplacement(
                pattern=r"from \. import (introspect|mixins|npyio|scimath)"
            ),
            RegexReplacement(
                pattern=r",\s+.({}).".format(
                    "|".join(
                        (
                            "add_newdoc",
                            "NumpyVersion",
                            "introspect",
                            "mixins",
                            "npyio",
                            "tracemalloc_domain",
                            "add_docstring",
                        )
                    )
                )
            ),
        },
        "numpy.linalg.__init__": {
            remove_numpy_pytester_re,
            RegexReplacement(pattern=r"from \. import linalg"),
        },
        "numpy.linalg._linalg": {
            RegexReplacement(pattern="from numpy._typing.*"),
            RegexReplacement(pattern=r",\s*.(qr|cholesky)."),
        },
        "numpy.matrixlib.__init__": {remove_numpy_pytester_re},
        "PIL.__init__": {
            RegexReplacement(
                pattern=r"_plugins = \[.*?\]",
                replacement="_plugins = []",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \. import _version.*del _version", flags=re.DOTALL
            ),
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
            RegexReplacement(
                pattern=r"try:\n    #.*?from \. import _imaging as core.*?except.*?raise",  # noqa: E501
                replacement="from . import _imaging as core",
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
            RegexReplacement(
                pattern=r"try:\s*Outline.*Outline = None", flags=re.DOTALL
            ),
            RegexReplacement(pattern="(L|l)ist, "),
            RegexReplacement(pattern="List", replacement="list"),
        },
        "PIL.ImageFile": {RegexReplacement(pattern="use_mmap = use_mmap.*")},
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
        "PIL.ImagePalette": {RegexReplacement(pattern="tostring = tobytes")},
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
    regex_to_apply_py["turbojpeg"].add(
        RegexReplacement(
            pattern=r"if platform.system\(\) == 'Linux'.*return lib_path",
            flags=re.DOTALL,
        )
    )

# Use platform since that what these modules check
if sys.platform != "linux":
    regex_to_apply_py["numpy.__init__"].add(
        RegexReplacement(
            pattern=r"def hugepage_setup\(\):.*?del hugepage_setup",
            replacement="_core.multiarray._set_madvise_hugepage(1)",
            flags=re.DOTALL,
        )
    )

# Keys are relative paths or globs. globs should target a single file
regex_to_apply_tk: defaultdict[str, set[RegexReplacement]] = defaultdict(
    set,
    {
        "tk/ttk/ttk.tcl": {
            # Loads themes that are not used
            RegexReplacement(
                pattern="proc ttk::LoadThemes.*?\n}",
                replacement="proc ttk::LoadThemes {} {}",
                flags=re.DOTALL,
            ),
        },
        "tcl8/*/platform-*.tm": {
            # Discontinued OS
            RegexReplacement(pattern=r"osf1 \{.*?\}", count=1, flags=re.DOTALL)
        },
    },
)

if sys.platform != "darwin":
    regex_to_apply_tk["tcl8/*/platform-*.tm"].add(
        RegexReplacement(pattern="set plat macosx", count=1)
    )

data_files_to_exclude: list[str] = [
    "tcl/http1.0",
    "tcl/tzdata",
    "tcl*/**/http-*.tm",
    "tcl*/**/shell-*.tm",
    "tcl*/**/tcltest-*.tm",
    "tk/ttk/*Theme.tcl",
    "tk/images",
    "tk/msgs",
]
if sys.platform != "darwin":
    # These are Mac specific encodings
    data_files_to_exclude.append("tcl/encoding/mac*.enc")

dlls_to_exclude: list[str] = ["libcrypto-*", "vcruntime*_1.dll"]
