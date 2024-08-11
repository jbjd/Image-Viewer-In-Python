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
    function_calls_to_skip,
    functions_to_skip,
    regex_to_apply_py,
    regex_to_apply_tk,
    vars_to_skip,
)
from compile_utils.file_operations import regex_replace
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

        node.bases = [
            base
            for base in node.bases
            if getattr(base, "id", "") not in ("ABC", "object")
        ]

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

        function_name: str = self._get_node_id_or_attr(node.func)
        if function_name not in self.func_calls_to_skip:
            super().visit_Call(node)
        else:
            super().visit_Pass(node)
            self.func_calls_to_skip[function_name] += 1

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
            self._node_is_doc_string_assign(node)
            or getattr(getattr(node.value, "func", object), "id", "")
            in self.func_calls_to_skip
        ):
            super().visit_Pass(node)
            return

        var_name: str = self._get_node_id_or_attr(node.targets[0])
        # TODO: Currently if a.b.c.d only "c" and "d" are checked
        parent_var_name: str = getattr(
            getattr(node.targets[0], "value", object), "attr", ""
        )
        if (
            var_name not in self.vars_to_skip
            and parent_var_name not in self.vars_to_skip
        ):
            super().visit_Assign(node)
        elif var_name in self.vars_to_skip:
            self.vars_to_skip[var_name] += 1
        else:
            self.vars_to_skip[parent_var_name] += 1

    @staticmethod
    def _node_is_doc_string_assign(node: ast.Assign) -> bool:
        return (
            isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr == "__doc__"
        )

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

        node.names = list(filter(lambda alias: alias.name != "__doc__", node.names))
        if not node.names:
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

    @staticmethod
    def _get_node_id_or_attr(node: ast.expr) -> str:
        """Gets id or attr which both can represent var/function names"""
        return getattr(node, "attr", "") or getattr(node, "id", "")


def clean_file_and_copy(path: str, new_path: str, module_name: str = "") -> None:
    with open(path, "r", encoding="utf-8") as fp:
        source: str = fp.read()

    # Remove module strings just so we have less to parse/write back to file
    source = re.sub(r"^\s*\"\"\".*?\"\"\"", "", source, count=1, flags=re.DOTALL)

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
