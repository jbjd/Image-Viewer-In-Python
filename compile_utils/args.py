import os
from argparse import REMAINDER, ArgumentParser, Namespace


class CustomArgParser(ArgumentParser):

    VALID_NUITKA_ARGS: set[str] = {
        "--mingw64",
        "--clang",
        "--standalone",
        "--enable-console",
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
                "Will not compile, will only create tmp directroy"
                "with cleaned .py files. This option is exposed for debugging"
            ),
        )
        self.add_argument("args", nargs=REMAINDER)

    def validate_and_return_arguments(self) -> tuple[Namespace, list[str]]:
        """Validates root privledge and no unknown arguments present"""
        args, nuitka_args = self.parse_known_args()

        if not args.debug:
            is_root: bool
            if os.name == "nt":
                import ctypes

                is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # On windows, mypy complains
                is_root = os.geteuid() == 0  # type: ignore

            if not is_root:
                raise PermissionError("need root privileges to compile and install")

        for extra_arg in nuitka_args:
            if extra_arg not in self.VALID_NUITKA_ARGS:
                raise ValueError(f"Unkown argument {extra_arg}")

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
            extra_args += " --nofollow-import-to=" + " --nofollow-import-to=".join(
                fp.read().strip().split("\n")
            )

    extra_args += (
        " --enable-console"
        if "--enable-console" in nuitka_args or args.debug
        else " --disable-console"
    )

    return extra_args
