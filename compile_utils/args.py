import os
from argparse import REMAINDER, ArgumentParser, Namespace

from compile_utils.validation import raise_if_not_root


class CompileArgParser(ArgumentParser):

    VALID_NUITKA_ARGS: set[str] = {
        "--mingw64",
        "--clang",
        "--standalone",
        "--enable-console",
        "--show-scons",
        "--show-memory",
    }

    def __init__(self, install_path: str) -> None:
        super().__init__(
            description="Compiles Personal Image Viewer to an executable",
            epilog=f"Some nuitka arguments are also accepted: {self.VALID_NUITKA_ARGS}",
        )

        default_python: str = "python" if os.name == "nt" else "python3"
        self.add_argument(
            "-p",
            "--python-path",
            help=f"Python to use in compilation, defaults to {default_python}",
            default=default_python,
        )
        self.add_argument(
            "--install-path", help=f"Path to install to, defaults to {install_path}"
        )
        self.add_argument(
            "--report",
            action="store_true",
            help="Adds --report=compilation-report.xml flag to nuitka",
        )
        self.add_argument(
            "--debug",
            action="store_true",
            help=(
                "Doesn't move compiled code to install path, doesn't check for root, "
                "doesn't pass Go, doesn't collect $200, "
                "adds --enable-console, --warn-implicit-exceptions, "
                "--warn-unusual-code, --report=compilation-report.xml flags to nuitka"
            ),
        )
        self.add_argument(
            "--skip-nuitka",
            action="store_true",
            help=(
                "Will not compile, will only create tmp directory"
                "with cleaned .py files. This option is exposed for debugging"
            ),
        )
        self.add_argument("args", nargs=REMAINDER)

    def validate_and_return_arguments(self) -> tuple[Namespace, list[str]]:
        """Validates root privilege and no unknown arguments present"""
        args, nuitka_args = self.parse_known_args()

        if not args.debug:
            raise_if_not_root()

        for extra_arg in nuitka_args:
            if extra_arg not in self.VALID_NUITKA_ARGS:
                raise ValueError(f"Unknown argument {extra_arg}")

        return args, nuitka_args


def parse_nuitka_args(args: Namespace, nuitka_args: list[str], working_dir: str) -> str:
    """Adds to nuitka args user passed for debugging and import skips"""
    extra_args: str = " ".join(nuitka_args).strip()

    if args.report or args.debug:
        extra_args += " --report=compilation-report.xml"
        if args.debug:
            extra_args += " --warn-implicit-exceptions --warn-unusual-code"

    if "--standalone" in nuitka_args:
        extra_args += " --enable-plugin=tk-inter"

        with open(os.path.join(working_dir, "skippable_imports.txt"), "r") as fp:
            imports_to_skip: list[str] = fp.read().strip().split("\n")

        SKIP_IMPORT_PREFIX: str = " --nofollow-import-to="
        extra_args += SKIP_IMPORT_PREFIX + SKIP_IMPORT_PREFIX.join(imports_to_skip)

    enable_conosle: bool = "--enable-console" in nuitka_args or args.debug
    extra_args += " --enable-console" if enable_conosle else " --disable-console"

    return extra_args
