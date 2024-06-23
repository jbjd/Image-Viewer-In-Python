import os
from argparse import REMAINDER, ArgumentParser, Namespace

from compile_utils.validation import raise_if_not_root


class CompileArgumentParser(ArgumentParser):
    """Argument Parser for compilation flags"""

    VALID_NUITKA_ARGS: set[str] = {
        "--mingw64",
        "--clang",
        "--msvc",
        "--standalone",
        "--quiet",
        "--verbose",
        "--show-scons",
        "--show-memory",
        "--windows-console-mode",
    }

    def __init__(self, install_path: str) -> None:
        super().__init__(
            description="Compiles Personal Image Viewer to an executable",
            epilog=f"Some nuitka arguments are also accepted: {self.VALID_NUITKA_ARGS}",
        )

        default_python: str = "python" if os.name == "nt" else "python3"
        self.add_argument(
            "--python-path",
            help=f"Python to use in compilation, defaults to {default_python}",
            default=default_python,
        )
        self.add_argument(
            "--install-path",
            help=f"Path to install to, defaults to {install_path}",
            default=install_path,
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
                "doesn't cleanup, doesn't pass Go, doesn't collect $200, "
                "adds --enable-console, --warn-implicit-exceptions, "
                "--warn-unusual-code, --report=compilation-report.xml flags to nuitka"
            ),
        )
        self.add_argument(
            "--skip-nuitka",
            action="store_true",
            help=(
                "Will not compile, will only create tmp directory "
                "with cleaned .py files. This option is exposed for debugging"
            ),
        )
        self.add_argument(
            "--no-cleanup",
            action="store_true",
            help=(
                "Does not delete temporary files used for build/distribtion"
                "This option is exposed for debugging"
            ),
        )
        self.add_argument("args", nargs=REMAINDER)

    # for some reason mypy gets the super type wrong
    def parse_known_args(  # type: ignore
        self, working_dir: str
    ) -> tuple[Namespace, list[str]]:
        """Returns Namespace of user arguments and string of args to pass to nuitka"""
        user_args, nuitka_args = super().parse_known_args()
        self._validate_args(nuitka_args, user_args.debug)

        nuitka_args = self._expand_nuitka_args(user_args, nuitka_args, working_dir)

        return user_args, nuitka_args

    def _validate_args(self, nuitka_args: list[str], debug: bool) -> None:
        """Validates root privilege and no unknown arguments present"""
        if not debug:
            raise_if_not_root()

        for extra_arg in nuitka_args:
            if extra_arg.split("=")[0] not in self.VALID_NUITKA_ARGS:
                raise ValueError(f"Unknown argument {extra_arg}")

    @staticmethod
    def _expand_nuitka_args(
        user_args: Namespace, nuitka_args: list[str], working_dir: str
    ) -> list[str]:
        """Given the input list of nuitka args, adds extra arguments
        based on flags user specified"""
        if user_args.report or user_args.debug:
            nuitka_args.append("--report=compilation-report.xml")
            if user_args.debug:
                nuitka_args += ["--warn-implicit-exceptions", "--warn-unusual-code"]

        if "--standalone" in nuitka_args:
            nuitka_args.append("--enable-plugin=tk-inter")

            with open(os.path.join(working_dir, "skippable_imports.txt"), "r") as fp:
                imports_to_skip: list[str] = fp.read().strip().split("\n")

            nuitka_args += [
                f"--nofollow-import-to={skipped_import}"
                for skipped_import in imports_to_skip
            ]

        ENABLE_CONSOLE: str = "--windows-console-mode=force"
        DISABLE_CONSOLE: str = "--windows-console-mode=disable"
        ATTACH_CONSOLE: str = "--windows-console-mode=attach"
        if (
            ENABLE_CONSOLE not in nuitka_args
            and DISABLE_CONSOLE not in nuitka_args
            and ATTACH_CONSOLE not in nuitka_args
        ):
            nuitka_args.append(ENABLE_CONSOLE if user_args.debug else DISABLE_CONSOLE)

        return nuitka_args
