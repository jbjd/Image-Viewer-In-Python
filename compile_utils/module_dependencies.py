"""Information on dependencies modules including:
* Dependencies based on current OS
* Modules that need to be explicitly included in standalone builds
* Modules that are not needed in standalone builds"""

import os

from personal_compile_tools.requirements import Requirement, parse_requirements_file

module_dependencies: list[Requirement] = parse_requirements_file("requirements.txt")

# Some modules can't be followed normally or need to
# be checked explicitly
modules_to_include: list[str] = ["image._jpeg_ext", "util._generic"]
if os.name == "nt":
    modules_to_include += ["util._os_nt"]

modules_to_skip: list[str] = [
    "argparse",
    "bz2",
    "csv",
    "email",
    "email.message",
    "email.parser",
    "hashlib",
    "lzma",
    "packaging",
    "PIL._deprecate",
    "PIL._typing",
    "PIL._version",
    "PIL.BdfFontFile",
    "PIL.BlpImagePlugin",
    "PIL.BmpImagePlugin",
    "PIL.BufrStubImagePlugin",
    "PIL.ContainerIO",
    "PIL.CurImagePlugin",
    "PIL.DcxImagePlugin",
    "PIL.EpsImagePlugin",
    "PIL.FitsImagePlugin",
    "PIL.FliImagePlugin",
    "PIL.FpxImagePlugin",
    "PIL.FtexImagePlugin",
    "PIL.GdImageFile",
    "PIL.GbrImagePlugin",
    "PIL.GribStubImagePlugin",
    "PIL.Hdf5StubImagePlugin",
    "PIL.IcnsImagePlugin",
    "PIL.IcoImagePlugin",
    "PIL.ImageGrab",
    "PIL.ImImagePlugin",
    "PIL.ImtImagePlugin",
    "PIL.IptcImagePlugin",
    "PIL.Jpeg2KImagePlugin",
    "PIL.McIdasImagePlugin",
    "PIL.MicImagePlugin",
    "PIL.MpegImagePlugin",
    "PIL.MpoImagePlugin",
    "PIL.MspImagePlugin",
    "PIL.PalmImagePlugin",
    "PIL.PcdImagePlugin",
    "PIL.PcfFontFile",
    "PIL.PcxImagePlugin",
    "PIL.PdfImagePlugin",
    "PIL.PdfParser",
    "PIL.PixarImagePlugin",
    "PIL.PpmImagePlugin",
    "PIL.PsdImagePlugin",
    "PIL.PSDraw",
    "PIL.QoiImagePlugin",
    "PIL.SgiImagePlugin",
    "PIL.SpiderImagePlugin",
    "PIL.SunImagePlugin",
    "PIL.TgaImagePlugin",
    "PIL.TiffImagePlugin",
    "PIL.WalImageFile",
    "PIL.WmfImagePlugin",
    "PIL.XbmImagePlugin",
    "PIL.XpmImagePlugin",
    "PIL.XVThumbImagePlugin",
    "PIL.FontFile",
    "PIL.ImageCms",
    "PIL.ImageDraw2",
    "PIL.ImageEnhance",
    "PIL.ImageFilter",
    "PIL.ImageMorph",
    "PIL.ImagePath",
    "PIL.ImageQt",
    "PIL.ImageShow",
    "PIL.ImageStat",
    "PIL.ImageTransform",
    "PIL.ImageWin",
    "PIL.TarIO",
    "PIL.features",
    "PIL.report",
    "py_compile",
    "pydoc",
    "select",
    "socket",
    "statistics",
    "urllib.error",
    "urllib.request",
]


if os.name == "nt":
    modules_to_skip += ["PIL._tkinter_finder", "selectors", "send2trash", "tempfile"]
else:
    # TODO: Skip everything but plat other?
    modules_to_skip += [
        "send2trash.mac",
        "send2trash.plat_gio",
        "send2trash.win",
    ]


def get_normalized_module_name(module: Requirement) -> str:
    """Given the name used for pip install,
    return the name used to import the module in python."""
    module_name: str = module.name.lower()

    return {"pillow": "PIL"}.get(module_name, module_name)
