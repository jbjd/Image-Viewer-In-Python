import ast
import os
import shutil
import subprocess
from _ast import Name
from argparse import REMAINDER, ArgumentParser
from glob import glob

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
    import nuitka  # noqa: F401
except ImportError:
    raise ImportError(
        "Nuitka is not installed on your system, it must be installed to compile"
    )

WORKING_DIR: str = f"{os.path.dirname(os.path.realpath(__file__))}/"
CODE_DIR: str = f"{WORKING_DIR}image_viewer/"
COMPILE_DIR: str = f"{WORKING_DIR}main.dist/"  # setup here, then copy to install path
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
        "adds --enable-console and --report=compilation-report.xml flags to nuitka"
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
    if args.debug and "--enable-console" not in extra_args_list:
        extra_args += " --enable-console"

if as_standalone:
    extra_args += " --enable-plugin=tk-inter"
    with open(os.path.join(WORKING_DIR, "skippable_imports.txt")) as fp:
        extra_args += " --nofollow-import-to=" + " --nofollow-import-to=".join(
            fp.read().strip().split("\n")
        )

extra_args += (
    " --enable-console"
    if "--enable-console" in extra_args_list
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
    shutil.rmtree(f"{WORKING_DIR}main.build/", ignore_errors=True)
    shutil.rmtree(f"{WORKING_DIR}main.dist/", ignore_errors=True)
    shutil.rmtree(f"{WORKING_DIR}tmp/", ignore_errors=True)
    try:
        os.remove(f"{WORKING_DIR}main.cmd")
    except FileNotFoundError:
        pass


class TypeHintRemover(ast._Unparser):
    """Functions copied from base class, edited to remove type hints"""

    def visit_FunctionDef(self, node):
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

    def visit_AnnAssign(self, node):
        if node.value:
            self.fill()
            with self.delimit_if(
                "(", ")", not node.simple and isinstance(node.target, Name)
            ):
                self.traverse(node.target)
            self.write(" = ")
            self.traverse(node.value)

    def visit_Import(self, node):
        if [n for n in node.names if n.name != "typing" and n.name != "collections"]:
            super().visit_Import(node)

    def visit_ImportFrom(self, node):
        if node.module != "typing" and node.module != "collections.abc":
            super().visit_ImportFrom(node)


# Before compiling, copy to tmp dir and remove type-hints
# I thought nuitka would handle this, but I guess not?
TMP_DIR: str = f"{WORKING_DIR}tmp/"
try:
    for python_file in glob(f"{CODE_DIR}**/*.py", recursive=True):
        new_path: str = python_file.replace("image_viewer", "tmp/image_viewer")

        with open(python_file) as fp:
            parsed_source = ast.parse(fp.read())
        contents: str = TypeHintRemover().visit(
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

    # Begin nuitka compilation in subprocess
    print("Starting compilation with nuitka")
    print("Using python install ", args.python_path)
    cmd_str = f'{args.python_path} -m nuitka --follow-import-to="factories" \
        --follow-import-to="helpers" --follow-import-to="util" --follow-import-to="ui" \
        --follow-import-to="viewer" --follow-import-to="managers" {extra_args} \
        --windows-icon-from-ico="{CODE_DIR}icon/icon.ico" \
        --warn-implicit-exceptions --warn-unusual-code \
        --python-flag="-OO,no_annotations,no_warnings" "{TMP_DIR}image_viewer/main.py"'

    process = subprocess.Popen(cmd_str, shell=True, cwd=WORKING_DIR)

    if args.install_path:
        INSTALL_PATH = args.install_path
    os.makedirs(INSTALL_PATH, exist_ok=True)

    print("Waiting for nuitka compilation...")
    process.wait()

    for data_file_path in DATA_FILE_PATHS:
        old_path = f"{CODE_DIR}{data_file_path}"
        new_path = f"{COMPILE_DIR}{data_file_path}"
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.copy(old_path, new_path)

    if args.debug:
        exit(0)

    if as_standalone:
        os.rename(
            f"{COMPILE_DIR}main{EXECUTABLE_EXT}", f"{COMPILE_DIR}viewer{EXECUTABLE_EXT}"
        )
    else:
        os.rename(
            f"{WORKING_DIR}main{EXECUTABLE_EXT}", f"{COMPILE_DIR}viewer{EXECUTABLE_EXT}"
        )
    shutil.rmtree(INSTALL_PATH, ignore_errors=True)
    os.rename(COMPILE_DIR, INSTALL_PATH)
finally:
    if not args.debug:
        clean_up()

print("\nFinished")
print("Installed to", INSTALL_PATH)
