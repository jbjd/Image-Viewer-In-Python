import ast
import importlib
import os
import shutil
import subprocess
from _ast import Name
from argparse import REMAINDER, ArgumentParser
from glob import glob
from sys import version_info

is_windows: bool = os.name == "nt"
if is_windows:
    import ctypes

try:
    import autoflake
except ImportError:
    print(
        "You do not have the autoflake package installed.",
        "Installing it will allow for a slightly smaller output\n",
    )
    autoflake = None

try:
    from nuitka import PythonVersions
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )

if version_info[:2] < (3, 10):
    raise Exception("Python 3.10 or higher required")

if (
    version := f"{version_info[0]}.{version_info[1]}"
) in PythonVersions.getNotYetSupportedPythonVersions():
    raise Exception(f"{version} not supported by Nuitka yet")

WORKING_DIR: str = os.path.abspath(os.path.dirname(__file__))
TMP_DIR: str = os.path.join(WORKING_DIR, "tmp")
CODE_DIR: str = os.path.join(WORKING_DIR, "image_viewer")
COMPILE_DIR: str = os.path.join(WORKING_DIR, "main.dist")
VALID_NUITKA_ARGS = {"--mingw64", "--clang", "--standalone", "--enable-console"}
INSTALL_PATH: str
EXECUTABLE_EXT: str
DATA_FILE_PATHS: list[str]

if is_windows:
    INSTALL_PATH = "C:/Program Files/Personal Image Viewer/"
    EXECUTABLE_EXT = ".exe"
    DATA_FILE_PATHS = ["icon/icon.ico", "dll/libturbojpeg.dll"]
else:
    INSTALL_PATH = "/usr/local/personal-image-viewer/"
    EXECUTABLE_EXT = ".bin"
    DATA_FILE_PATHS = ["icon/icon.png"]

parser = ArgumentParser(
    description="Compiles Personal Image Viewer to an executable, must be run as root",
    epilog=f"Some nuitka arguments are also accepted: {VALID_NUITKA_ARGS}\n",
)
parser.add_argument("-p", "--python-path", help="Python path to use in compilation")
parser.add_argument(
    "--install-path", help=f"Path to install to, default is {INSTALL_PATH}"
)
parser.add_argument(
    "--report",
    action="store_true",
    help="Adds --report=compilation-report.xml flag to nuitka",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help=(
        "Doesn't move compiled code to install path, doesn't check for root, "
        "doesn't pass Go, doesn't collect $200, "
        "adds --enable-console, --warn-implicit-exceptions, --warn-unusual-code,"
        " --report=compilation-report.xml flags to nuitka"
    ),
)
parser.add_argument("args", nargs=REMAINDER)
args, extra_args_list = parser.parse_known_args()
for extra_arg in extra_args_list:
    if extra_arg not in VALID_NUITKA_ARGS:
        raise ValueError(f"Unkown arguement {extra_arg}")

extra_args: str = " ".join(extra_args_list).strip()
as_standalone: bool = "--standalone" in extra_args_list

if args.report or args.debug:
    extra_args += " --report=compilation-report.xml"
    if args.debug:
        extra_args += " --warn-implicit-exceptions --warn-unusual-code"

if as_standalone:
    extra_args += " --enable-plugin=tk-inter"
    with open(os.path.join(WORKING_DIR, "skippable_imports.txt")) as fp:
        extra_args += " --nofollow-import-to=" + " --nofollow-import-to=".join(
            fp.read().strip().split("\n")
        )

extra_args += (
    " --enable-console"
    if "--enable-console" in extra_args_list or args.debug
    else " --disable-console"
)

if not args.debug:
    is_root: bool
    if is_windows:
        is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        # On windows, mypy complains
        is_root = os.geteuid() == 0  # type: ignore

    if not is_root:
        raise Exception("compile.py needs root privileges to run")

if args.python_path is None:
    if is_windows:
        # if not provided, try to find with where
        args.python_path = (
            subprocess.run("where python", shell=True, stdout=subprocess.PIPE)
            .stdout.decode()
            .partition("\n")[0]
        )
        if args.python_path == "":
            raise Exception(
                (
                    "Failed to find path to python. "
                    "Please provide the --python-path command line argument"
                )
            )
    else:
        args.python_path = "python3"


def clean_up() -> None:
    shutil.rmtree(os.path.join(WORKING_DIR, "main.build"), ignore_errors=True)
    shutil.rmtree(COMPILE_DIR, ignore_errors=True)
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    try:
        os.remove(os.path.join(WORKING_DIR, "main.cmd"))
    except FileNotFoundError:
        pass


skip_repo = {
    "turbojpeg": (
        {},
        {"crop_multiple", "scale_with_quality", "decode_to_yuv_planes"},
    )
}


class TypeHintRemover(ast._Unparser):
    """Functions copied from base class, mainly edited to remove type hints"""

    def __init__(self, module_name: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        if module_name in skip_repo:
            self.vars_to_skip, self.func_to_skip = skip_repo[module_name]
        else:
            self.vars_to_skip = {}
            self.func_to_skip = {}

    def visit_FunctionDef(self, node):
        """Removes type hints from functions"""
        if node.name in self.func_to_skip:
            return
        self.maybe_newline()
        for deco in node.decorator_list:
            self.fill("@")
            self.traverse(deco)
        self.fill(f"def {node.name}")
        if node.args.args:
            for arg in node.args.args:
                arg.annotation = None
        with self.delimit("(", ")"):
            self.traverse(node.args)
        with self.block(extra=self.get_type_comment(node)):
            self._write_docstring_and_traverse_body(node)

    def visit_Assign(self, node):
        """Skips over some variables"""
        var_name: str = getattr(node.targets[0], "id", "")
        if var_name not in self.vars_to_skip:
            super().visit_Assign(node)

    def visit_AnnAssign(self, node):
        """Remove var annotations and declares like 'var: type' without an = after"""
        if node.value:
            self.fill()
            with self.delimit_if(
                "(", ")", not node.simple and isinstance(node.target, Name)
            ):
                self.traverse(node.target)
            self.write(" = ")
            self.traverse(node.value)

    def visit_Import(self, node):
        """Skips writing type hinting imports"""
        if [n for n in node.names if n.name != "typing" and n.name != "collections"]:
            super().visit_Import(node)

    def visit_ImportFrom(self, node):
        """Skips writing type hinting imports"""
        if node.module != "typing" and node.module != "collections.abc":
            super().visit_ImportFrom(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path) as fp:
        parsed_source = ast.parse(fp.read())
    contents: str = TypeHintRemover(module_name).visit(
        ast.NodeTransformer().visit(parsed_source)
    )

    if autoflake:
        contents = autoflake.fix_code(
            contents,
            remove_all_unused_imports=True,
            remove_duplicate_keys=True,
            remove_unused_variables=True,
            remove_rhs_for_unused_variables=True,
        )

    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    with open(new_path, "w") as fp:
        fp.write(contents)


def move_files_to_tmp_and_clean(dir: str, mod_prefix: str = ""):
    for python_file in glob(f"{dir}/**/*.py", recursive=True):
        if os.path.basename(python_file) == "__main__.py" and mod_prefix != "":
            continue
        python_file = os.path.abspath(python_file)
        relative_path: str = os.path.join(
            mod_prefix, python_file.replace(dir, "").strip("/\\")
        )
        new_path: str = os.path.join(TMP_DIR, relative_path)
        clean_file_and_copy(python_file, new_path)


# Before compiling, copy to tmp dir and remove type-hints/clean code
# I thought nuitka would handle this, but I guess not?
shutil.rmtree(TMP_DIR, ignore_errors=True)
try:
    move_files_to_tmp_and_clean(CODE_DIR)

    for mod_name in ["turbojpeg", "send2trash"]:  # TODO: add more
        module = importlib.import_module(mod_name)
        base_file_name: str = os.path.basename(module.__file__)
        if base_file_name == "__init__.py":
            # its really a folder
            move_files_to_tmp_and_clean(os.path.dirname(module.__file__), mod_name)
        else:
            # its just one file
            clean_file_and_copy(
                module.__file__,
                os.path.join(TMP_DIR, base_file_name),
                mod_name,
            )

    # Begin nuitka compilation in subprocess
    print("Starting compilation with nuitka")
    print("Using python install ", args.python_path)
    cmd_str = f'{args.python_path} -m nuitka --follow-import-to="factories" \
        --follow-import-to="helpers" --follow-import-to="util" --follow-import-to="ui" \
        --follow-import-to="viewer" --follow-import-to="managers" {extra_args} \
        --windows-icon-from-ico="{CODE_DIR}/icon/icon.ico" \
        --python-flag="-OO,no_annotations,no_warnings" "{TMP_DIR}/main.py"'

    process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

    if args.install_path:
        INSTALL_PATH = args.install_path
    os.makedirs(INSTALL_PATH, exist_ok=True)

    print("Waiting for nuitka compilation...")
    process.wait()

    for data_file_path in DATA_FILE_PATHS:
        old_path = os.path.join(CODE_DIR, data_file_path)
        new_path = os.path.join(COMPILE_DIR, data_file_path)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)

    if args.debug:
        exit(0)

    dest: str = os.path.join(COMPILE_DIR, f"viewer{EXECUTABLE_EXT}")
    src: str = os.path.join(
        COMPILE_DIR if as_standalone else WORKING_DIR, f"main{EXECUTABLE_EXT}"
    )
    os.rename(src, dest)
    shutil.rmtree(INSTALL_PATH, ignore_errors=True)
    os.rename(COMPILE_DIR, INSTALL_PATH)
finally:
    if not args.debug:
        clean_up()

print("\nFinished")
print("Installed to", INSTALL_PATH)
