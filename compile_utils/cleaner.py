"""Classes and functions that remove unused code and annotations"""

import ast
import os
import re
import warnings
from _ast import Name
from glob import glob
from re import sub
from shutil import copyfile

from compile_utils.code_to_skip import (
    classes_to_skip,
    dict_keys_to_skip,
    folders_to_exlcude,
    function_calls_to_skip,
    functions_to_skip,
    globs_to_exlucde,
    regex_to_apply,
    vars_to_skip,
)
from compile_utils.file_operations import (
    delete_file_globs,
    delete_folders,
    regex_replace,
)
from compile_utils.regex import RegexReplacement

try:
    import autoflake
except ImportError:
    warnings.warn(
        (
            "You do not have the autoflake package installed. "
            "Installing it will allow for a slightly smaller output\n"
        )
    )
    autoflake = None

if os.name == "nt":
    separators = r"[\\/]"
else:
    separators = r"[/]"


class CleanUnpsarser(ast._Unparser):  # type: ignore
    """Functions copied from base class, mainly edited to remove type hints"""

    VARS_TRACKING_REMOVED = [
        "func_to_skip",
        "vars_to_skip",
        "classes_to_skip",
        "func_calls_to_skip",
    ]

    def __init__(self, module_name: str = "") -> None:
        super().__init__()

        # dict to track if provided values are used
        self.func_to_skip: dict[str, int] = {
            k: 0 for k in functions_to_skip[module_name]
        }
        self.vars_to_skip: dict[str, int] = {k: 0 for k in vars_to_skip[module_name]}
        self.classes_to_skip: dict[str, int] = {
            k: 0 for k in classes_to_skip[module_name]
        }
        self.func_calls_to_skip: dict[str, int] = {
            k: 0 for k in function_calls_to_skip[module_name]
        }
        self.dict_keys_to_skip: dict[str, int] = {
            k: 0 for k in dict_keys_to_skip[module_name]
        }

        self.write_annotations_without_value: bool = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Disable removing annotations within class vars for safety"""
        if node.name in self.classes_to_skip:
            self.classes_to_skip[node.name] += 1
            return

        node.bases = [base for base in node.bases if getattr(base, "id", "") != "ABC"]

        # Remove class doc strings to speed up writing to file
        if isinstance(node.body[0], ast.Expr) and isinstance(
            node.body[0].value, ast.Constant
        ):
            node.body[0].value.value = ""

        self.write_annotations_without_value = True
        super().visit_ClassDef(node)
        self.write_annotations_without_value = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Skips some functions and removes type hints from the rest"""
        if node.name in self.func_to_skip:
            self.func_to_skip[node.name] += 1
            return

        # Remove doc string to speed up parse/write
        if isinstance(node.body[0], ast.Expr) and isinstance(
            node.body[0].value, ast.Constant
        ):
            node.body = node.body[1:]
            if not node.body:
                super().visit_Pass(node)
                return

        argument: ast.arg
        for argument in node.args.args:
            argument.annotation = None
        node.returns = None

        # always ignore inside of function context
        previous_ignore: bool = self.write_annotations_without_value

        self.write_annotations_without_value = False
        super().visit_FunctionDef(node)
        self.write_annotations_without_value = previous_ignore

    def visit_Call(self, node: ast.Call) -> None:
        # Skips warnings.warn() calls
        if self._node_is_logging(node):
            super().visit_Pass(node)
            return
        if (
            getattr(node.func, "attr", "") not in self.func_calls_to_skip
            and getattr(node.func, "id", "") not in self.func_calls_to_skip
        ):
            super().visit_Call(node)
        else:
            super().visit_Pass(node)
            self.func_calls_to_skip[
                getattr(node.func, "attr", "") or getattr(node.func, "id", "")
            ] += 1

    @staticmethod
    def _node_is_logging(node: ast.Call) -> bool:
        return (
            getattr(node.func, "attr", "") in ("warn", "filterwarnings", "simplefilter")
            and getattr(node.func, "value", ast.Name("")).id == "warnings"
        ) or (
            getattr(node.func, "attr", "") == "debug"
            and "log" in getattr(node.func, "value", ast.Name("")).id
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Skips over some variables"""
        if getattr(getattr(node.value, "func", object), "attr", "") == "getLogger":
            return

        if (
            getattr(getattr(node.value, "func", object), "id", "")
            in self.func_calls_to_skip
        ):
            super().visit_Pass(node)
            return

        var_name: str = getattr(node.targets[0], "id", "")
        if var_name not in self.vars_to_skip:
            super().visit_Assign(node)
        else:
            self.vars_to_skip[var_name] += 1

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Remove var annotations and declares like 'var: type' without an = after"""
        if node.value or self.write_annotations_without_value:
            var_name: str = getattr(node.target, "id", "")
            if var_name in self.vars_to_skip:
                self.vars_to_skip[var_name] += 1
                return
            self.fill()
            with self.delimit_if(
                "(", ")", not node.simple and isinstance(node.target, Name)
            ):
                self.traverse(node.target)
            if node.value:
                self.write(" = ")
                self.traverse(node.value)
            else:
                # Can only reach here if annotation must be kept for formatting a class
                self.write(": ")
                # These might refer to removed things, so make them all something
                placeholder_id: str = '"Any"'
                new_node = ast.Name(id=placeholder_id, ctx=None)  # type: ignore
                self.traverse(new_node)

    def visit_If(self, node: ast.If) -> None:
        # Skip if __name__ = "__main__"
        try:
            if node.test.left.id == "__name__":  # type: ignore
                return
        except AttributeError:
            pass

        # Skip PIL's blocks about typechecking
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            if node.orelse:
                super().traverse(node.orelse)
            return

        super().visit_If(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Skip unnecessary futures imports"""
        if node.module == "__future__":
            return

        super().visit_ImportFrom(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        """Replace some dict constants"""
        if self.dict_keys_to_skip:
            new_dict = {
                k: v
                for k, v in zip(node.keys, node.values)
                if getattr(k, "value", "") not in self.dict_keys_to_skip
            }
            node.keys = list(new_dict.keys())
            node.values = list(new_dict.values())
        super().visit_Dict(node)


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    # TODO #6: Find all triple quotes strings, not just ones that start a file
    source = re.sub(r"^\s*\"\"\".*?\"\"\"", "", source, flags=re.DOTALL)

    if module_name in regex_to_apply:
        regex_and_replacement: set[RegexReplacement] = regex_to_apply[module_name]
        for regex, replacement, flags in regex_and_replacement:
            source, count_replaced = re.subn(regex, replacement, source, flags=flags)
            if count_replaced == 0:
                warnings.warn(f"{module_name}: Unused regex\n{regex}\n")

    parsed_source: ast.Module = ast.parse(source)
    code_cleaner = CleanUnpsarser(module_name)
    source = code_cleaner.visit(ast.NodeTransformer().visit(parsed_source))

    # Check for code that was marked to ksip, but was not found in the module
    for var in code_cleaner.VARS_TRACKING_REMOVED:
        tracker = getattr(code_cleaner, var)
        unused_but_requested: set[str] = {k for k, v in tracker.items() if v == 0}
        if unused_but_requested:
            warnings.warn(
                (
                    f"{module_name}: {','.join(unused_but_requested)} requested to skip"
                    f" in {var} but was not present"
                )
            )

    if autoflake is not None:
        # Numpy often imports other imports which this would break
        edit_imports: bool = module_name[:5] != "numpy"
        source = autoflake.fix_code(
            source,
            remove_all_unused_imports=edit_imports,
            remove_duplicate_keys=True,
            remove_unused_variables=True,
            remove_rhs_for_unused_variables=True,
        )

    with open(new_path, "w", encoding="utf-8") as fp:
        fp.write(source)


def move_files_to_tmp_and_clean(
    dir: str, tmp_dir: str, mod_prefix: str, modules_to_skip: list[str] | None = None
) -> None:
    """Moves python files from dir to temp_dir and removes unused/unneeded code"""
    if modules_to_skip is None:
        modules_to_skip = []

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
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        if python_file.endswith(".py"):
            mod_name: str = sub(separators, ".", relative_path)[:-3]  # chops of .py
            if mod_name in modules_to_skip:
                continue
            elif "." in mod_name:
                package_name: str = mod_name[: mod_name.rfind(".")]
                if package_name in modules_to_skip:
                    continue
            clean_file_and_copy(python_file, new_path, mod_name)
        else:
            copyfile(python_file, new_path)


def clean_or_delete_auto_included_files(compile_dir: str) -> None:
    """Removes unwanted files that nuitka auto includes in standalone
    and cleans up comments/whitespace from necesary tcl files"""
    # tcl/tzdata is for timezones, which are not used in this program
    # tk/images contains the tk logo
    absolute_folders_to_exclude: list[str] = [
        os.path.join(compile_dir, rel_path) for rel_path in folders_to_exlcude
    ]
    delete_folders(absolute_folders_to_exclude)

    absolute_globs_to_exclude: list[str] = [
        os.path.join(compile_dir, rel_path) for rel_path in globs_to_exlucde
    ]
    delete_file_globs(absolute_globs_to_exclude)

    # Removing unused Tk code so we can delete more unused files
    regex_replace(
        os.path.join(compile_dir, "tk/ttk/ttk.tcl"),
        RegexReplacement(
            pattern="proc ttk::LoadThemes.*?\n}",
            replacement="proc ttk::LoadThemes {} {}",
            flags=re.DOTALL,
        ),
    )

    # delete comments in tcl files
    strip_comments = RegexReplacement(
        pattern=r"^\s*#.*", replacement="", flags=re.MULTILINE
    )
    strip_whitespace = RegexReplacement(
        pattern=r"\n\s+", replacement="\n", flags=re.MULTILINE
    )
    strip_starting_whitespace = RegexReplacement(pattern=r"^\s+", replacement="")
    strip_consecutive_whitespace = RegexReplacement(
        pattern="[ \t][ \t]+", replacement=" "
    )

    for code_file in glob(os.path.join(compile_dir, "**/*.tcl"), recursive=True) + glob(
        os.path.join(compile_dir, "**/*.tm"), recursive=True
    ):
        regex_replace(
            code_file,
            [
                strip_comments,
                strip_whitespace,
                strip_starting_whitespace,
                strip_consecutive_whitespace,
            ],
        )

    regex_replace(os.path.join(compile_dir, "tcl/tclIndex"), strip_whitespace)
