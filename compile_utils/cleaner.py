"""Classes and functions that remove unused code and annotations"""

import ast
import os
import re
import warnings
from glob import glob
from re import sub
from shutil import copyfile

from personal_python_minifier.parser import MinifyUnparser
from personal_python_minifier.flake_wrapper import run_autoflake

from compile_utils.code_to_skip import (
    classes_to_skip,
    dict_keys_to_skip,
    from_imports_to_skip,
    functions_to_skip,
    regex_to_apply_py,
    regex_to_apply_tk,
    vars_to_skip,
)
from compile_utils.file_operations import regex_replace
from compile_utils.regex import RegexReplacement
from compile_utils.validation import MINIMUM_PYTHON_VERSION


if os.name == "nt":
    separators = r"[\\/]"
else:
    separators = r"[/]"


class CleanUnpsarser(MinifyUnparser):  # type: ignore
    """Removes various bits of unneeded code like type hints"""

    def __init__(self, module_name: str = "") -> None:
        super().__init__(
            target_python_version=MINIMUM_PYTHON_VERSION,
            skip_name_equals_main=True,
            functions_to_skip=functions_to_skip[module_name],
            vars_to_skip=vars_to_skip[module_name],
            classes_to_skip=classes_to_skip[module_name],
            from_imports_to_skip=from_imports_to_skip[module_name],
            dict_keys_to_skip=dict_keys_to_skip[module_name],
        )

        if module_name == "numpy.lib.array_utils":
            pass

    def visit_Pass(self, node: ast.Pass | None = None) -> None:
        super().visit_Pass(node if node else ast.Pass())

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Remove ABC since its basically a parent class no-op
        base_classes_to_ignore: list[str] = ["ABC"]
        super().visit_ClassDef(node, base_classes_to_ignore=base_classes_to_ignore)

    def visit_Call(self, node: ast.Call) -> None:
        # Skips logging/warnings
        if self._node_is_logging(node):
            self.visit_Pass()
            return

        super().visit_Call(node)

    @staticmethod
    def _node_is_logging(node: ast.Call) -> bool:
        return (
            getattr(node.func, "attr", "") in ("warn", "filterwarnings", "simplefilter")
            and getattr(node.func, "value", ast.Name("")).id == "warnings"
        ) or (
            getattr(node.func, "attr", "") == "debug"
            and "log" in getattr(node.func, "value", ast.Name("")).id
        )

    def visit_If(self, node: ast.If) -> None:
        # Skip PIL's blocks about typechecking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            if node.orelse:
                super().traverse(node.orelse)
            return

        super().visit_If(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    if module_name in regex_to_apply_py:
        regex_and_replacement: set[RegexReplacement] = regex_to_apply_py[module_name]
        for regex, replacement, flags, count in regex_and_replacement:
            source, count_replaced = re.subn(
                regex, replacement, source, flags=flags, count=count
            )
            if count_replaced == 0:
                warnings.warn(f"{module_name}: Unused regex\n{regex}\n")

    parsed_source: ast.Module = ast.parse(source)
    code_cleaner = CleanUnpsarser(module_name)
    source = code_cleaner.visit(ast.NodeTransformer().visit(parsed_source))

    edit_imports: bool = module_name[:5] != "numpy"
    source = run_autoflake(source, remove_unused_imports=edit_imports)

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(source)


def move_files_to_tmp_and_clean(
    dir: str, tmp_dir: str, mod_prefix: str, modules_to_skip: set[str] | None = None
) -> None:
    """Moves python files from dir to temp_dir and removes unused/unneeded code"""
    if modules_to_skip:
        modules_to_skip_re = rf"^({'|'.join(modules_to_skip)})($|\.)"
    else:
        modules_to_skip_re = ""

    for python_file in iter(
        os.path.abspath(p)
        for p in glob(f"{dir}/**/*", recursive=True)
        if p.endswith((".py", ".pyd"))
    ):
        if os.path.basename(python_file) == "__main__.py" and mod_prefix != "":
            continue  # skip __main__ in modules other than this one

        relative_path: str = os.path.join(
            mod_prefix, python_file.replace(dir, "").strip("/\\")
        )
        new_path: str = os.path.join(tmp_dir, relative_path)
        dir_path: str = os.path.dirname(new_path)

        mod_name: str = sub(separators, ".", relative_path)[:-3]  # chops .py

        if modules_to_skip is not None and (
            skip_match := re.match(modules_to_skip_re, mod_name)
        ):
            match: str = skip_match.string[: skip_match.end()]
            if match[-1] == ".":
                match = match[:-1]
            if match in modules_to_skip:
                modules_to_skip.remove(match)
            continue

        os.makedirs(dir_path, exist_ok=True)
        if python_file.endswith(".py"):
            clean_file_and_copy(python_file, new_path, mod_name)
        else:
            copyfile(python_file, new_path)

    if modules_to_skip:
        warnings.warn(
            "Some imports where marked to skip but not found: "
            + " ".join(modules_to_skip)
        )


def clean_tk_files(compile_dir: str) -> None:
    """Removes unwanted files that nuitka auto includes in standalone
    and cleans up comments/whitespace from necesary tcl files"""
    for path_or_glob, regexs in regex_to_apply_tk.items():
        glob_result: list[str] = glob(os.path.join(compile_dir, path_or_glob))
        if not glob_result:
            warnings.warn(f"{path_or_glob}: Glob not found")
            continue

        # globs are used since files may have versioning in name
        # They are intended to target a single file
        code_file: str = glob_result[0]
        regex_replace(code_file, regexs)

    # delete comments in tcl files
    strip_comments = RegexReplacement(pattern=r"^\s*#.*", flags=re.MULTILINE)
    strip_whitespace = RegexReplacement(
        pattern=r"\n\s+", replacement="\n", flags=re.MULTILINE
    )
    strip_consecutive_whitespace = RegexReplacement(
        pattern="[ \t][ \t]+", replacement=" "
    )
    remove_prints = RegexReplacement(pattern="^(puts|parray) .*", flags=re.MULTILINE)
    clean_up_new_lines = RegexReplacement(pattern="\n\n+", replacement="\n")
    clean_up_starting_new_line = RegexReplacement(pattern="^\n", count=1)

    for code_file in glob(os.path.join(compile_dir, "**/*.tcl"), recursive=True) + glob(
        os.path.join(compile_dir, "**/*.tm"), recursive=True
    ):
        regex_replace(
            code_file,
            [
                strip_comments,
                strip_whitespace,
                strip_consecutive_whitespace,
                remove_prints,
                clean_up_new_lines,
                clean_up_starting_new_line,
            ],
        )

    regex_replace(os.path.join(compile_dir, "tcl/tclIndex"), strip_whitespace)
