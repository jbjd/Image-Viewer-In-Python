"""Collections of various bits of code that should not be included during compilation"""

import os
import platform
import re
import sys
from collections import defaultdict

from personal_python_minifier.regex import RegexReplacement
from turbojpeg import DEFAULT_LIB_PATHS as turbojpeg_platforms

_skip_functions_kwargs: dict[str, set[str]] = {
    "numpy.__init__": {"__dir__", "_pyinstaller_hooks_dir", "filterwarnings"},
    "numpy._core._exceptions": {"_display_as_base"},
    "numpy._core.arrayprint": {
        "_array_repr_dispatcher",
        "_array_repr_implementation",
        "_array_str_dispatcher",
        "_array2string_dispatcher",
        "_get_legacy_print_mode",
        "_set_printoptions",
        "_void_scalar_to_string",
        "array_repr",
        "dtype_short_repr",
        "get_printoptions",
        "printoptions",
        "set_printoptions",
    },
    "numpy._core.function_base": {
        "_add_docstring",
        "_geomspace_dispatcher",
        "_linspace_dispatcher",
        "_logspace_dispatcher",
        "_needs_add_docstring",
        "add_newdoc",
    },
    "numpy._core.getlimits": {"__repr__"},
    "numpy._core.numeric": {"_frombuffer", "_full_dispatcher"},
    "numpy._core.numerictypes": {"maximum_sctype"},
    "numpy._core.overrides": {"add_docstring", "verify_matching_signatures"},
    "numpy._core.records": {"__repr__", "__str__", "pprint"},
    "numpy._core.strings": {
        "_join",
        "_rsplit",
        "_split",
        "_splitlines",
    },
    "numpy._globals": {"__repr__"},
    "numpy.lib._arraysetops_impl": {
        "_ediff1d_dispatcher",
        "_in1d_dispatcher",
        "_intersect1d_dispatcher",
        "_isin_dispatcher",
        "_setdiff1d_dispatcher",
        "_setxor1d_dispatcher",
        "_union1d_dispatcher",
        "_unique_all_dispatcher",
        "_unique_counts_dispatcher",
        "_unique_dispatcher",
        "_unique_inverse_dispatcher",
        "_unique_values_dispatcher",
        "ediff1d",
    },
    "numpy.lib._histograms_impl": {
        "_histogram_bin_edges_dispatcher",
        "_histogram_dispatcher",
        "_histogramdd_dispatcher",
        "histogram_bin_edges",
    },
    "numpy.lib._shape_base_impl": {
        "_array_split_dispatcher",
        "_hvdsplit_dispatcher",
        "_kron_dispatcher",
        "_put_along_axis_dispatcher",
        "_replace_zero_by_x_arrays",
        "_split_dispatcher",
        "_take_along_axis_dispatcher",
        "_tile_dispatcher",
    },
    "numpy.lib._stride_tricks_impl": {
        "_broadcast_arrays_dispatcher",
        "_broadcast_to_dispatcher",
        "_sliding_window_view_dispatcher",
    },
    "numpy.linalg._linalg": {
        "_cond_dispatcher",
        "_convertarray",
        "_cholesky_dispatcher",
        "_eigvalsh_dispatcher",
        "_matrix_power_dispatcher",
        "_outer_dispatcher",
        "_qr_dispatcher",
        "_raise_linalgerror_qr",
        "_solve_dispatcher",
        "_svd_dispatcher",
        "_tensorinv_dispatcher",
        "_tensorsolve_dispatcher",
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
    "PIL.features": {
        "check",
        "check_codec",
        "check_feature",
        "get_supported",
        "get_supported_codecs",
        "get_supported_features",
        "get_supported_modules",
        "pilinfo",
        "version",
        "version_codec",
        "version_feature",
    },
    "PIL.Image": {
        "__getstate__",
        "__repr__",
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
        "debug",
        "deprecate",
        "entropy",
        "fromqimage",
        "fromqpixmap",
        "getexif",
        "getLogger",
        "getxmp",
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
    "PIL.ImageMath": {"deprecate", "eval", "unsafe_eval"},
    "PIL.ImageMode": {"deprecate"},
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
    "PIL.ImageTk": {"_get_image_from_kw", "_show"},
    "PIL.DdsImagePlugin": {"register_decoder"},
    "PIL.GifImagePlugin": {"_save_netpbm", "getheader", "register_mime"},
    "PIL.JpegImagePlugin": {
        "_getexif",
        "_save_cjpeg",
        "deprecate",
        "load_djpeg",
        "register_mime",
    },
    "PIL.PngImagePlugin": {"debug", "getLogger", "register_mime"},
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
    "numpy._array_api_info": {"__module__"},
    "numpy._core.arrayprint": {"__docformat__", "_default_array_repr"},
    "numpy._core.multiarray": {"__module__"},
    "numpy._core.numerictypes": {"genericTypeRank"},
    "numpy._core.overrides": {"array_function_like_doc", "ArgSpec"},
    "numpy._core.records": {"__module__", "numfmt"},
    "numpy.lib._function_base_impl": {"__doc__"},
    "numpy.lib._shape_base_impl": {"__doc__"},
    "numpy.linalg._linalg": {"__doc__", "array_function_dispatch", "fortran_int"},
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
    "PIL.features": {"codecs", "features"},
    "PIL.Image": {"MIME"},
    "PIL.GifImagePlugin": {"format_description", "_Palette"},
    "PIL.JpegImagePlugin": {"format_description"},
    "PIL.PngImagePlugin": {"format_description"},
    "PIL.WebPImagePlugin": {"format_description"},
}

_skip_classes_kwargs: dict[str, set[str]] = {
    "helpers.action_undoer": {"ABC"},
    "numpy.exceptions": {"ModuleDeprecationWarning", "RankWarning"},
    "PIL.DdsImagePlugin": {"DdsRgbDecoder"},
    "PIL.Image": {"SupportsArrayInterface", "SupportsGetData"},
    "PIL.ImageFile": {
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

_skip_from_imports: dict[str, set[str]] = {
    "numpy.__init__": {
        "__array_namespace_info__",
        "__version__",
        "_distributor_init",
        "array_repr",
        "c_",
        "ediff1d",
        "einsum",
        "einsum_path",
        "matrixlib",
        "r_",
        "s_",
        "version",
    },
    "numpy._core.__init__": {"version"},
    "numpy._core._methods": {"_exceptions"},
    "numpy._core.function_base": {"add_docstring"},
    "numpy._core.numerictypes": {
        "LOWER_TABLE",
        "UPPER_TABLE",
        "_kind_name",
        "english_capitalize",
        "english_lower",
        "english_upper",
        "object",
    },
    "numpy._core.overrides": {"getargspec"},
    "numpy._core.records": {"_get_legacy_print_mode"},
    "numpy.lib.stride_tricks": {"__doc__"},
    "numpy.linalg.__init__": {"linalg"},
    "PIL.features": {"deprecate"},
    "PIL.ImageMath": {"deprecate"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.JpegImagePlugin": {"deprecate"},
}

_skip_dict_keys_kwargs: dict[str, set[str]] = {
    "turbojpeg": {k for k in turbojpeg_platforms if k != platform.system()}
}

_skip_decorators_kwargs: dict[str, set[str]] = {
    "numpy._core._exceptions": {"_display_as_base"},
    "numpy._core._ufunc_config": {"set_module", "wraps"},
    "numpy._core.arrayprint": {"array_function_dispatch", "set_module", "wraps"},
    "numpy._core.fromnumeric": {"array_function_dispatch", "set_module"},
    "numpy._core.function_base": {"array_function_dispatch"},
    "numpy._core.getlimits": {"set_module"},
    "numpy._core.multiarray": {"array_function_from_c_func_and_dispatcher"},
    "numpy._core.numeric": {
        "array_function_dispatch",
        "set_array_function_like_doc",
        "set_module",
    },
    "numpy._core.numerictypes": {"set_module"},
    "numpy._core.records": {"set_module"},
    "numpy._core.shape_base": {"array_function_dispatch"},
    "numpy.lib._arraysetops_impl": {"array_function_dispatch"},
    "numpy.lib._function_base_impl": {"array_function_dispatch", "set_module"},
    "numpy.lib._histograms_impl": {"array_function_dispatch"},
    "numpy.lib._index_tricks_impl": {"array_function_dispatch", "set_module"},
    "numpy.lib._nanfunctions_impl": {"array_function_dispatch"},
    "numpy.lib._shape_base_impl": {"array_function_dispatch", "set_module"},
    "numpy.lib._stride_tricks_impl": {"array_function_dispatch", "set_module"},
    "numpy.lib._twodim_base_impl": {
        "array_function_dispatch",
        "set_array_function_like_doc",
        "set_module",
    },
    "numpy.lib._type_check_impl": {"array_function_dispatch", "set_module"},
    "numpy.lib._ufunclike_impl": {"array_function_dispatch"},
    "numpy.linalg._linalg": {"array_function_dispatch", "set_module"},
    "numpy.matrixlib.defmatrix": {"set_module"},
    "PIL.Image": {"abstractmethod"},
}


decorators_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_decorators_kwargs
)
dict_keys_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_dict_keys_kwargs
)
functions_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_functions_kwargs
)
vars_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_vars_kwargs)
classes_to_skip: defaultdict[str, set[str]] = defaultdict(set, **_skip_classes_kwargs)
from_imports_to_skip: defaultdict[str, set[str]] = defaultdict(
    set, **_skip_from_imports
)


remove_all_re = RegexReplacement(pattern=".*", flags=re.DOTALL)
remove_numpy_pytester_re = RegexReplacement(
    pattern=r"\s*from numpy._pytesttester import PytestTester.*?del PytestTester",
    flags=re.DOTALL,
)
regex_to_apply_py: defaultdict[str, list[RegexReplacement]] = defaultdict(
    list,
    {
        "util.PIL": [RegexReplacement(pattern=r"_Image._plugins = \[\]")],
        "numpy.__init__": [
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
            RegexReplacement(
                pattern=", (_CopyMode|show_config|histogram_bin_edges|memmap|require)"
            ),
            RegexReplacement(pattern=r"from \.lib import .*"),
            RegexReplacement(
                pattern=r"from \.(lib\.(_arraypad_impl|_npyio_impl|_utils_impl|_polynomial_impl)|matrixlib) import .*?\)",  # noqa E501
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"__numpy_submodules__ =.*?\}", count=1, flags=re.DOTALL
            ),
            RegexReplacement(pattern=r"(get)?(set)?_?printoptions,", count=3),
        ]
        + [
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
        ],
        "numpy._core.__init__": [
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"if not.*raise ImportError\(msg.format\(path\)\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \. import (_add_newdocs|_internal|_dtype).*"
            ),
            RegexReplacement(pattern=r"from \.memmap import \*", count=1),
            RegexReplacement(
                pattern=r"except ImportError as exc:.*?raise ImportError\(msg\)",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r".*?einsumfunc.*",
            ),
        ],
        "numpy._core._ufunc_config": [
            RegexReplacement(
                "def _no_nep50_warning.*",
                "def _no_nep50_warning():yield",
                flags=re.DOTALL,
            )
        ],
        "numpy._core.arrayprint": [
            RegexReplacement(pattern=", .array_repr."),
            RegexReplacement(pattern=r"['\"](get)?(set)?_?printoptions['\"],", count=3),
        ],
        "numpy._core.numeric": [
            RegexReplacement(pattern=".*_asarray.*", count=3),
        ],
        "numpy._core.overrides": [
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
                pattern="def decorator.*?return public_api",
                replacement="def decorator(i): return i",
                flags=re.DOTALL,
            ),
        ],
        "numpy._globals": [RegexReplacement(".*?_set_module.*")],
        "numpy._utils.__init__": [
            RegexReplacement(
                pattern="^.*",
                replacement="""
def set_module(_):
    def d(f):return f
    return d""",
                flags=re.DOTALL,
            )
        ],
        "numpy.lib.__init__": [
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
        ],
        "numpy.lib.array_utils": [
            RegexReplacement(
                "^.*",
                """
from numpy._core.numeric import normalize_axis_tuple,normalize_axis_index
__all__=['normalize_axis_tuple','normalize_axis_index']""",
                flags=re.DOTALL,
            )
        ],
        "numpy.linalg.__init__": [remove_numpy_pytester_re],
        "numpy.linalg._linalg": [
            RegexReplacement(pattern="from numpy._typing.*"),
            RegexReplacement(pattern=r",\s*.(qr|cholesky)."),
        ],
        "numpy.matrixlib.__init__": [remove_numpy_pytester_re],
        "PIL.__init__": [
            RegexReplacement(
                pattern=r"_plugins = \[.*?\]",
                replacement="_plugins = []",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \. import _version.*del _version", flags=re.DOTALL
            ),
        ],
        "PIL.GifImagePlugin": [
            RegexReplacement(
                pattern="from typing import .*",
                replacement="from collections import namedtuple",
            ),
            RegexReplacement(
                pattern=r"_Frame\(NamedTuple\)",
                replacement="_Frame(namedtuple('_Frame', ['im', 'bbox', 'encoderinfo']))",  # noqa E501
            ),
        ],
        "PIL.Image": [
            RegexReplacement(
                pattern="""try:
    from defusedxml import ElementTree
except ImportError:
    ElementTree = None""",
            ),
            RegexReplacement(pattern="from ._deprecate import deprecate"),
            RegexReplacement(
                pattern=r"try:\n    #.*?from \. import _imaging as core.*?except.*?raise",  # noqa: E501
                replacement="from . import _imaging as core",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"def preinit\(\).*_initialized = 1", flags=re.DOTALL
            ),
        ],
        "PIL.ImageDraw": [
            RegexReplacement(pattern="_Ink =.*"),
            RegexReplacement(
                pattern=r"def Draw.*?return ImageDraw.*?\)",
                replacement="""def Draw(im, mode=None): return ImageDraw(im, mode)""",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"try:\s*Outline.*Outline = None", flags=re.DOTALL
            ),
            RegexReplacement(pattern="(L|l)ist, "),  # codespell:ignore ist
            RegexReplacement(pattern="List", replacement="list"),
        ],
        "PIL.ImageFile": [
            RegexReplacement(pattern="use_mmap = use_mmap.*"),
            RegexReplacement(
                pattern="from typing import .*",
                replacement="""
from typing import IO, cast
from collections import namedtuple""",
                count=1,
            ),
            RegexReplacement(
                pattern=r"_Tile\(NamedTuple\):",
                replacement="_Tile(namedtuple('_Tile', ['codec_name', 'extents', 'offset', 'args'])):",  # noqa E501
                count=1,
            ),
        ],
        "PIL.ImageMode": [
            RegexReplacement(
                pattern="from typing import NamedTuple",
                replacement="from collections import namedtuple",
            ),
            RegexReplacement(
                pattern=r"\(NamedTuple\):",
                replacement=r"(namedtuple('ModeDescriptor', ['mode', 'bands', 'basemode', 'basetype', 'typestr'])):",  # noqa E501
            ),
        ],
        "PIL.ImagePalette": [RegexReplacement(pattern="tostring = tobytes")],
        "PIL.PngImagePlugin": [
            RegexReplacement(
                pattern=r"raise EOFError\(.*?\)", replacement="raise EOFError"
            ),
            RegexReplacement(
                pattern="from typing import .*",
                replacement="from typing import IO, cast\nfrom collections import namedtuple",  # noqa E501
            ),
            RegexReplacement(
                pattern=r"_RewindState\(NamedTuple\)",
                replacement="_RewindState(namedtuple('_RewindState', ['info', 'tile', 'seq_num']))",  # noqa E501
            ),
            RegexReplacement(
                pattern=r"_Frame\(NamedTuple\)",
                replacement="_Frame(namedtuple('_Frame', ['im', 'bbox', 'encoderinfo']))",  # noqa E501
            ),
        ],
        "send2trash.__init__": [remove_all_re],
        "send2trash.win.__init__": [remove_all_re],
        # Fix issue with autoflake
        "send2trash.compat": [
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
        ],
        # We don't use pathlib's Path, remove support for it
        "send2trash.util": [RegexReplacement(pattern=r".*\[path\.__fspath__\(\).*\]")],
    },
)
if os.name == "nt":
    regex_to_apply_py["turbojpeg"].append(
        RegexReplacement(
            pattern=r"if platform.system\(\) == 'Linux'.*return lib_path",
            flags=re.DOTALL,
        )
    )

# Use platform since that what these modules check
if sys.platform != "linux":
    regex_to_apply_py["numpy.__init__"].append(
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
