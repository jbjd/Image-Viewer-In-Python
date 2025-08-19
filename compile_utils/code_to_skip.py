"""Collections of various bits of code that should not be included during compilation"""

import os
import re
import sys
from collections import defaultdict

from personal_python_ast_optimizer.regex.classes import RegexReplacement

from compile_utils.package_info import IMAGE_VIEWER_NAME
from image_viewer.constants import TEXT_RGB

functions_to_skip: dict[str, set[str]] = {
    "PIL._binary": {"i8", "si16be", "si16le", "si32be", "si32le"},
    "PIL._util": {"new"},
    "PIL.AvifImagePlugin": {"get_codec_version", "register_mime"},
    "PIL.Image": {
        "__arrow_c_array__",
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
        "fromarrow",
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

if os.name == "nt":
    vars_to_skip["PIL.AvifImagePlugin"] = {"DEFAULT_MAX_THREADS"}


classes_to_skip: dict[str, set[str]] = {
    f"{IMAGE_VIEWER_NAME}.actions.types": {"ABC"},
    f"{IMAGE_VIEWER_NAME}.state.base": {"ABC"},
    f"{IMAGE_VIEWER_NAME}.ui.base": {"ABC"},
    "PIL.Image": {
        "SupportsArrayInterface",
        "SupportsArrowArrayInterface",
        "SupportsGetData",
    },
    "PIL.ImageFile": {
        "Parser",
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
    "PIL.Image": {"deprecate"},
    "PIL.ImageMath": {"deprecate"},
    "PIL.ImageMode": {"deprecate"},
    "PIL.JpegImagePlugin": {"deprecate"},
}

dict_keys_to_skip: dict[str, set[str]] = {}

decorators_to_skip: dict[str, set[str]] = {
    f"{IMAGE_VIEWER_NAME}.ui.base": {"abstractmethod"},
    "PIL.Image": {"abstractmethod"},
}

module_imports_to_skip: dict[str, set[str]] = {}


constants_to_fold: defaultdict[str, dict[str, int | str]] = defaultdict(
    dict,
    {
        IMAGE_VIEWER_NAME: {
            "DEFAULT_ANIMATION_SPEED_MS": 100,
            "DEFAULT_BACKGROUND_COLOR": "#000000",
            "DEFAULT_MAX_ITEMS_IN_CACHE": 20,
            "JPEG_MAX_DIMENSION": 65_535,
            "TEXT_RGB": TEXT_RGB,
        },
    },
)

remove_all_re = RegexReplacement(pattern="^.*$", flags=re.DOTALL)
regex_to_apply_py: defaultdict[str, list[RegexReplacement]] = defaultdict(
    list,
    {
        f"{IMAGE_VIEWER_NAME}.util.PIL": [
            RegexReplacement(pattern=r"_Image._plugins = \[\]")
        ],
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
                replacement="from typing import cast;from collections import namedtuple",  # noqa E501
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
        "PIL.JpegImagePlugin": [
            RegexReplacement(  # Remove .mpo support for now
                r"def jpeg_factory\(.*return im",
                "def jpeg_factory(fp,filename=None):return JpegImageFile(fp,filename)",
                flags=re.DOTALL,
            )
        ],
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
    regex_to_apply_py["PIL.AvifImagePlugin"] = [
        RegexReplacement(
            r"def _get_default_max_threads\(\).*?or 1",
            "def _get_default_max_threads():return os.cpu_count() or 1",
            flags=re.DOTALL,
            count=1,
        )
    ]
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
    regex_to_apply_py["send2trash.exceptions"] = [
        RegexReplacement(
            pattern="^.*$",
            replacement="""
import errno
class TrashPermissionError(PermissionError):
    def __init__(self, filename):
        PermissionError.__init__(self, errno.EACCES, "Permission denied", filename)""",
            flags=re.DOTALL,
            count=1,
        )
    ]
    # We don't use pathlib's Path, remove support for it
    regex_to_apply_py["send2trash.util"] = [
        RegexReplacement(pattern=r".*\[path\.__fspath__\(\).*\]")
    ]


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
