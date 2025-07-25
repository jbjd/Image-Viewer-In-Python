"""Collections of various bits of code that should not be included during compilation"""

import os
import platform
import re
import sys
from collections import defaultdict

from personal_python_ast_optimizer.regex.classes import RegexReplacement
from turbojpeg import DEFAULT_LIB_PATHS as turbojpeg_platforms

from compile_utils.package_info import IMAGE_VIEWER_NAME
from image_viewer.animation.frame import DEFAULT_ANIMATION_SPEED_MS
from image_viewer.config import DEFAULT_BACKGROUND_COLOR, DEFAULT_MAX_ITEMS_IN_CACHE
from image_viewer.constants import TEXT_RGB

_JPEG_MAX_DIMENSION = 65_535
_OAIF_EXEC = 4
_OAIF_HIDE_REGISTRATION = 32

functions_to_skip: dict[str, set[str]] = {
    "numpy.__init__": {
        "__dir__",
        "_pyinstaller_hooks_dir",
        "_reload_guard",
        "filterwarnings",
    },
    "numpy._core.__init__": {"set_typeDict"},
    "numpy._core._exceptions": {"_display_as_base"},
    "numpy._core._machar": {"__str__"},
    "numpy._core._methods": {
        "_all",
        "_amax",
        "_amin",
        "_any",
        "_clip",
        "_prod",
        "_sum",
    },
    "numpy._core.arrayprint": {
        "_array_repr_dispatcher",
        "_array_repr_implementation",
        "_array_str_dispatcher",
        "_array2string_dispatcher",
        "_get_legacy_print_mode",
        "_set_printoptions",
        "_void_scalar_to_string",
        "array_repr",
        "dtype_is_implied",
        "dtype_short_repr",
        "get_printoptions",
        "printoptions",
        "set_printoptions",
    },
    "numpy._core.getlimits": {"_discovered_machar", "_get_machar"},
    "numpy._core.fromnumeric": {
        "_all_dispatcher",
        "_any_dispatcher",
        "_argmax_dispatcher",
        "_argmin_dispatcher",
        "_argpartition_dispatcher",
        "_argsort_dispatcher",
        "_choose_dispatcher",
        "_clip_dispatcher",
        "_compress_dispatcher",
        "_cumprod_dispatcher",
        "_cumsum_dispatcher",
        "_cumulative_prod_dispatcher",
        "_cumulative_sum_dispatcher",
        "_diagonal_dispatcher",
        "_matrix_transpose_dispatcher",
        "_max_dispatcher",
        "_mean_dispatcher",
        "_min_dispatcher",
        "_ndim_dispatcher",
        "_nonzero_dispatcher",
        "_partition_dispatcher",
        "_prod_dispatcher",
        "_ptp_dispatcher",
        "_put_dispatcher",
        "_ravel_dispatcher",
        "_repeat_dispatcher",
        "_reshape_dispatcher",
        "_resize_dispatcher",
        "_round_dispatcher",
        "_searchsorted_dispatcher",
        "_shape_dispatcher",
        "_size_dispatcher",
        "_sort_dispatcher",
        "_squeeze_dispatcher",
        "_std_dispatcher",
        "_sum_dispatcher",
        "_swapaxes_dispatcher",
        "_take_dispatcher",
        "_trace_dispatcher",
        "_transpose_dispatcher",
        "_var_dispatcher",
    },
    "numpy._core.numeric": {
        "_allclose_dispatcher",
        "_argwhere_dispatcher",
        "_array_equal_dispatcher",
        "_array_equiv_dispatcher",
        "_astype_dispatcher",
        "_convolve_dispatcher",
        "_correlate_dispatcher",
        "_count_nonzero_dispatcher",
        "_cross_dispatcher",
        "_flatnonzero_dispatcher",
        "_frombuffer",
        "_full_dispatcher",
        "_full_like_dispatcher",
        "_isclose_dispatcher",
        "_moveaxis_dispatcher",
        "_ones_like_dispatcher",
        "_outer_dispatcher",
        "_roll_dispatcher",
        "_rollaxis_dispatcher",
        "_tensordot_dispatcher",
        "_zeros_like_dispatcher",
        "cross",
        "extend_all",
    },
    "numpy._core.numerictypes": {"maximum_sctype"},
    "numpy._core.overrides": {"add_docstring", "verify_matching_signatures"},
    "numpy._core.records": {
        "__repr__",
        "__str__",
        "array",
        "fromfile",
        "fromrecords",
        "fromstring",
        "pprint",
    },
    "numpy._core.shape_base": {
        "_arrays_for_stack_dispatcher",
        "_atleast_1d_dispatcher",
        "_atleast_2d_dispatcher",
        "_atleast_3d_dispatcher",
        "_block_dispatcher",
        "_stack_dispatcher",
        "_unstack_dispatcher",
        "_vhstack_dispatcher",
        "atleast_3d",
    },
    "numpy._globals": {"__repr__"},
    "numpy.lib._stride_tricks_impl": {
        "_broadcast_arrays_dispatcher",
        "_broadcast_to_dispatcher",
        "_sliding_window_view_dispatcher",
        "sliding_window_view",
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
    "PIL._binary": {"i8", "si16be", "si16le", "si32be", "si32le"},
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
        "_expand",
        "_repr_image",
        "_repr_jpeg_",
        "_repr_pretty_",
        "_repr_png_",
        "_show",
        "alpha_composite",
        "blend",
        "composite",
        "debug",
        "deprecate",
        "effect_mandelbrot",
        "entropy",
        "fromqimage",
        "fromqpixmap",
        "get_child_images",
        "getexif",
        "getLogger",
        "getmodebandnames",
        "getxmp",
        "linear_gradient",
        "load_from_fp",
        "putalpha",
        "radial_gradient",
        "register_mime",
        "show",
        "toqimage",
        "toqpixmap",
    },
    "PIL.ImageChops": {
        "add",
        "add_modulo",
        "blend",
        "composite",
        "constant",
        "darker",
        "difference",
        "duplicate",
        "hard_light",
        "invert",
        "lighter",
        "logical_and",
        "logical_or",
        "logical_xor",
        "multiply",
        "offset",
        "overlay",
        "screen",
        "soft_light",
        "subtract",
    },
    "PIL.ImageDraw": {"_color_diff", "getdraw", "floodfill"},
    "PIL.ImageFile": {"get_format_mimetype", "verify", "raise_oserror"},
    "PIL.ImageFont": {
        "__getstate__",
        "__setstate__",
        "getmetrics",
        "load_default_imagefont",
        "load_default",
        "load_path",
    },
    "PIL.ImageMath": {"deprecate", "eval", "unsafe_eval"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.ImageOps": {
        "_color",
        "autocontrast",
        "colorize",
        "contain",
        "cover",
        "deform",
        "equalize",
        "expand",
        "exif_transpose",
        "grayscale",
        "mirror",
        "pad",
        "posterize",
        "solarize",
    },
    "PIL.ImagePalette": {
        "load",
        "make_gamma_lut",
        "make_linear_lut",
        "negative",
        "random",
        "sepia",
        "wedge",
    },
    "PIL.ImageTk": {"_get_image_from_kw", "getimage"},
    "PIL.DdsImagePlugin": {"register_decoder"},
    "PIL.GifImagePlugin": {"_save_netpbm", "getheader", "register_mime"},
    "PIL.JpegImagePlugin": {
        "_getexif",
        "_save_cjpeg",
        "deprecate",
        "load_djpeg",
        "register_mime",
    },
    "PIL.PngImagePlugin": {"debug", "deprecate", "getLogger", "register_mime"},
    "PIL.WebPImagePlugin": {"register_mime"},
    "PIL.TiffTags": {"_populate"},
}


vars_to_skip: dict[str, set[str]] = {
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
    "numpy._core.__init__": {"__all__"},
    "numpy._core._methods": {"bool_dt"},
    "numpy._core.arrayprint": {"__docformat__", "_default_array_repr", "_typelessdata"},
    "numpy._core.fromnumeric": {"array_function_dispatch"},
    "numpy._core.getlimits": {"_convert_to_float"},
    "numpy._core.multiarray": {
        "__all__",
        "__module__",
        "array_function_from_c_func_and_dispatcher",
    },
    "numpy._core.numerictypes": {"genericTypeRank"},
    "numpy._core.overrides": {"ArgSpec", "array_function_like_doc"},
    "numpy._core.records": {"__all__", "__module__", "numfmt"},
    "numpy._core.shape_base": {"__all__", "array_function_dispatch"},
    "numpy.exceptions": {"__all__", "_is_loaded"},
    "turbojpeg": {
        "__author__",
        "__buffer_size_YUV2",
        "__compressFromYUV",
        "__decompressToYUVPlanes",
        "__decompressToYUV2",
        "__version__",
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
    "PIL.Image": {"MIME", "TYPE_CHECKING"},
    "PIL.ImageDraw": {"Outline", "TYPE_CHECKING"},
    "PIL.ImageFile": {"TYPE_CHECKING"},
    "PIL.ImageFont": {"TYPE_CHECKING"},
    "PIL.ImagePalette": {"TYPE_CHECKING"},
    "PIL.ImageTk": {"TYPE_CHECKING"},
    "PIL.GifImagePlugin": {"TYPE_CHECKING", "_Palette", "format_description"},
    "PIL.JpegImagePlugin": {"TYPE_CHECKING", "format_description"},
    "PIL.PngImagePlugin": {"TYPE_CHECKING", "format_description"},
    "PIL.WebPImagePlugin": {"format_description"},
}


classes_to_skip: dict[str, set[str]] = {
    f"{IMAGE_VIEWER_NAME}.actions.types": {"ABC"},
    f"{IMAGE_VIEWER_NAME}.state.base": {"ABC"},
    f"{IMAGE_VIEWER_NAME}.ui.base": {"ABC"},
    "numpy._core.getlimits": {"finfo", "iinfo"},
    # Hidden use of ComplexWarning, VisibleDeprecationWarning
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
    "PIL.PngImagePlugin": {"PngInfo"},
    f"{IMAGE_VIEWER_NAME}.state.base": {"StateBase"},
    f"{IMAGE_VIEWER_NAME}.state.rotation_state": {"StateBase"},
    f"{IMAGE_VIEWER_NAME}.state.zoom_state": {"StateBase"},
}


from_imports_to_skip: dict[str, set[str]] = {
    "numpy.__init__": {
        "__array_namespace_info__",
        "__version__",
        "_distributor_init",
        "asmatrix",
        "bmat",
        "fix",
        "get_include",
        "histogram",
        "histogramdd",
        "info",
        "isneginf",
        "isposinf",
        "matrixlib",
        "matrix",
        "pad",
        "show_runtime",
        "version",
    },
    "numpy._core.__init__": {
        "_add_newdocs",
        "_add_newdocs_scalars",
        "_dtype",
        "_dtype_ctypes",
        "_internal",
        "_methods",
        "function_base",
        "version",
    },
    "numpy._core._ufunc_config": {"set_module"},
    "numpy._core.arrayprint": {"set_module"},
    "numpy._core.fromnumeric": {"set_module"},
    "numpy._core.getlimits": {"set_module"},
    "numpy._core.numeric": {"_asarray", "set_module"},
    "numpy._core.numerictypes": {
        "LOWER_TABLE",
        "UPPER_TABLE",
        "_kind_name",
        "english_capitalize",
        "english_lower",
        "english_upper",
        "object",
        "set_module",
    },
    "numpy._core.overrides": {"getargspec", "set_module"},
    "numpy._core.records": {"_get_legacy_print_mode", "set_module"},
    "numpy._core.umath": {"_add_newdoc_ufunc"},
    "numpy.lib._stride_tricks_impl": {
        "array_function_dispatch",
        "normalize_axis_tuple",
        "set_module",
    },
    "PIL.features": {"deprecate"},
    "PIL.Image": {"deprecate"},
    "PIL.ImageMath": {"deprecate"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.JpegImagePlugin": {"deprecate"},
}

dict_keys_to_skip: dict[str, set[str]] = {
    "PIL.features": {"tkinter"},
    "turbojpeg": {k for k in turbojpeg_platforms if k != platform.system()},
}

decorators_to_skip: dict[str, set[str]] = {
    f"{IMAGE_VIEWER_NAME}.ui.base": {"abstractmethod"},
    "numpy._core._exceptions": {"_display_as_base"},
    "numpy._core._ufunc_config": {"set_module", "wraps"},
    "numpy._core.arrayprint": {"array_function_dispatch", "set_module", "wraps"},
    "numpy._core.fromnumeric": {"array_function_dispatch", "set_module"},
    "numpy._core.multiarray": {"array_function_from_c_func_and_dispatcher"},
    "numpy._core.numeric": {
        "array_function_dispatch",
        "finalize_array_function_like",
        "set_module",
    },
    "numpy._core.numerictypes": {"set_module"},
    "numpy._core.records": {"set_module"},
    "numpy._core.shape_base": {"array_function_dispatch"},
    "numpy.lib._stride_tricks_impl": {"array_function_dispatch", "set_module"},
    "PIL.Image": {"abstractmethod"},
}

module_imports_to_skip: dict[str, set[str]] = {
    "numpy.__init__": {
        "_expired_attrs_2_0",
        "lib._arraysetops_impl",
        "lib._function_base_impl",
        "lib._index_tricks_impl",
        "lib._nanfunctions_impl",
        "lib._npyio_impl",
        "lib._polynomial_impl",
        "lib._shape_base_impl",
        "lib._twodim_base_impl",
        "lib._type_check_impl",
        "lib",
    },
    "numpy._core.__init__": {"function_base"},
    "numpy._core.numeric": {"_asarray"},
    "numpy._core.overrides": {"numpy._core._multiarray_umath"},
    "numpy._core.umath": {"numpy"},
}


constants_to_fold: defaultdict[str, dict[str, int | str]] = defaultdict(
    dict,
    {
        IMAGE_VIEWER_NAME: {
            "DEFAULT_ANIMATION_SPEED_MS": DEFAULT_ANIMATION_SPEED_MS,
            "DEFAULT_BACKGROUND_COLOR": DEFAULT_BACKGROUND_COLOR,
            "DEFAULT_MAX_ITEMS_IN_CACHE": DEFAULT_MAX_ITEMS_IN_CACHE,
            "JPEG_MAX_DIMENSION": _JPEG_MAX_DIMENSION,
            "OAIF_EXEC": _OAIF_EXEC,
            "OAIF_HIDE_REGISTRATION": _OAIF_HIDE_REGISTRATION,
            "TEXT_RGB": TEXT_RGB,
        }
    },
)

remove_all_re = RegexReplacement(pattern="^.*$", flags=re.DOTALL)
remove_numpy_pytester_re = RegexReplacement(
    pattern=r"\s*from numpy._pytesttester import PytestTester.*?del PytestTester",
    flags=re.DOTALL,
)
regex_to_apply_py: defaultdict[str, list[RegexReplacement]] = defaultdict(
    list,
    {
        f"{IMAGE_VIEWER_NAME}.util.PIL": [
            RegexReplacement(pattern=r"_Image._plugins = \[\]")
        ],
        "numpy.__init__": [
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=(
                    r"if attr == .linalg.:.*?"
                    r"AttributeError\(f.module \{__name__!r\} has no attribute .*?\)"
                ),
                replacement="""if attr=='dtypes':
            import numpy.dtypes as dtypes
            return dtypes
        elif attr=='exceptions':
            import numpy.exceptions as exceptions
            return exceptions
        raise AttributeError('module {!r} has no attribute {!r}'.format(__name__,attr))""",  # noqa E501
                flags=re.DOTALL,
            ),
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
                pattern=", (_CopyMode|show_config|histogram_bin_edges|memmap|require|geomspace|logspace|cross)"  # noqa E501
            ),
            RegexReplacement(
                pattern=r"__numpy_submodules__ =.*?\}", count=1, flags=re.DOTALL
            ),
            RegexReplacement(pattern=r"(get)?(set)?_?printoptions,", count=3),
            RegexReplacement(
                pattern=r"from \._core import \(.*?\)",
                replacement="from ._core import *",
                flags=re.DOTALL,
                count=1,
            ),
        ],
        "numpy._core.__init__": [
            remove_numpy_pytester_re,
            RegexReplacement(
                pattern=r"env_added = \[\].*?del env_added",
                flags=re.DOTALL,
                count=1,
            ),
            RegexReplacement(
                pattern=(
                    r"if not \(hasattr\(multiarray.*"
                    r"raise ImportError\(msg.format\(path\)\)"
                ),
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern=r"from \.memmap import \*",
                replacement="from .numeric import uint8",
                count=1,
            ),
            RegexReplacement(
                pattern=r".*?einsumfunc.*",
            ),
        ],
        "numpy._core.arrayprint": [
            RegexReplacement(
                r"__all__ = \[.*?\]",
                "__all__=['array2string','array_str','format_float_positional','format_float_scientific']",  # noqa E501
                flags=re.DOTALL,
                count=1,
            ),
            RegexReplacement(
                """try:
    from _thread import get_ident
except ImportError:
    from _dummy_thread import get_ident""",
                "from _thread import get_ident",
                count=1,
            ),
        ],
        "numpy._core.getlimits": [
            RegexReplacement(pattern="__all__.*", replacement="__all__=[]")
        ],
        "numpy._core.numeric": [
            RegexReplacement(pattern=r"extend_all\(_asarray\)", count=1),
            RegexReplacement(pattern=".cross.,", count=1),
        ],
        "numpy._core.overrides": [
            RegexReplacement(
                pattern="def get_array_function_like_doc.*?return public_api",
                replacement="def finalize_array_function_like(a):return a",
                flags=re.DOTALL,
            ),
            RegexReplacement(
                pattern="def decorator.*?return public_api",
                replacement="def decorator(i):return i",
                count=1,
                flags=re.DOTALL,
            ),
        ],
        "numpy._globals": [RegexReplacement(".*?_set_module.*")],
        "numpy.lib.__init__": [remove_all_re],
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
                count=1,
            ),
            RegexReplacement(
                pattern=r"_Frame\(NamedTuple\)",
                replacement="_Frame(namedtuple('_Frame',['im','bbox','encoderinfo']))",  # noqa E501
                count=1,
            ),
        ],
        "PIL.Image": [
            RegexReplacement(
                pattern="""try:
    from defusedxml import ElementTree
except ImportError:
    ElementTree = None""",
            ),
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
                replacement="""def Draw(im,mode=None):return ImageDraw(im,mode)""",
                count=1,
                flags=re.DOTALL,
            ),
            RegexReplacement(pattern="(L|l)ist, "),  # codespell:ignore ist
            RegexReplacement(pattern="List", replacement="list"),
        ],
        "PIL.ImageFile": [
            RegexReplacement(
                pattern="from typing import .*",
                replacement="""from typing import IO, cast
from collections import namedtuple""",
                count=1,
            ),
            RegexReplacement(
                pattern=r"_Tile\(NamedTuple\):",
                replacement="_Tile(namedtuple('_Tile', ['codec_name', 'extents', 'offset', 'args'])):",  # noqa E501
                count=1,
            ),
        ],
        "PIL.ImageFont": [
            RegexReplacement(
                pattern=r"try:.*DeferredError\.new\(ex\)",
                replacement="from . import _imagingft as core",
                flags=re.DOTALL,
            ),
            RegexReplacement(pattern=r"MAX_STRING_LENGTH is not None and"),
            RegexReplacement(
                pattern=r"""try:\s+from packaging\.version import parse as parse_version
.*?DeprecationWarning,\s+\)""",
                flags=re.DOTALL,
            ),
        ],
        "PIL.ImageMode": [
            RegexReplacement(
                pattern="from typing import NamedTuple",
                replacement="from collections import namedtuple",
                count=1,
            ),
            RegexReplacement(
                pattern=r"\(NamedTuple\):",
                replacement=r"(namedtuple('ModeDescriptor', ['mode', 'bands', 'basemode', 'basetype', 'typestr'])):",  # noqa E501
                count=1,
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
    },
)
if os.name == "nt":
    regex_to_apply_py["turbojpeg"].append(
        RegexReplacement(
            pattern=r"if platform.system\(\) == 'Linux'.*return lib_path",
            flags=re.DOTALL,
        )
    )
else:
    regex_to_apply_py["send2trash.__init__"] = [remove_all_re]
    regex_to_apply_py["send2trash.compat"] = [  # Fix issue with autoflake
        RegexReplacement(
            pattern="^.*$",
            replacement=(
                """
text_type = str
binary_type = bytes
from collections.abc import Iterable
iterable_type = Iterable"""
                + ("" if os.name == "nt" else "\nimport os\nenvironb = os.environb")
            ),
            flags=re.DOTALL,
            count=1,
        ),
    ]
    # We don't use pathlib's Path, remove support for it
    regex_to_apply_py["send2trash.util"] = [
        RegexReplacement(pattern=r".*\[path\.__fspath__\(\).*\]")
    ]

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
            RegexReplacement(pattern=r"osf1 \{.*?\}", count=1, flags=re.DOTALL),
            RegexReplacement(
                pattern=r"solaris(\*-\*)? \{(.*?\{.*?\}.*?)*?\}", flags=re.DOTALL
            ),
        },
    },
)

if sys.platform != "darwin":
    regex_to_apply_tk["tcl8/*/platform-*.tm"].add(
        RegexReplacement(
            pattern=r"darwin \{.*?aix", replacement="aix", flags=re.DOTALL, count=1
        )
    )

    regex_to_apply_tk["tcl/auto.tcl"].add(
        RegexReplacement(
            pattern=r'if \{\$tcl_platform\(platform\) eq "unix".*?\}.*?\}',
            flags=re.DOTALL,
            count=1,
        )
    )

    regex_to_apply_tk["tcl/init.tcl"].add(
        RegexReplacement(
            pattern=r'if \{\$tcl_platform\(os\) eq "Darwin".*?else.*?\}\s*?\}',
            replacement="package unknown {::tcl::tm::UnknownHandler ::tclPkgUnknown}",
            flags=re.DOTALL,
            count=1,
        )
    )

data_files_to_exclude: list[str] = [
    "tcl/http1.0",
    "tcl/tzdata",
    "tcl*/**/http-*.tm",
    "tcl*/**/shell-*.tm",
    "tcl*/**/tcltest-*.tm",
    "tcl/parray.tcl",
    "tk/ttk/*Theme.tcl",
    "tk/images",
    "tk/msgs",
]
if sys.platform != "darwin":
    # These are Mac specific encodings
    data_files_to_exclude.append("tcl/encoding/mac*.enc")

dlls_to_exclude: list[str] = ["libcrypto-*", "vcruntime*_1.dll"]
