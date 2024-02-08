import ast
import os
import warnings
from _ast import Name

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

skip_repo: dict[str, tuple] = {
    "turbojpeg": (
        {},
        {"crop_multiple", "scale_with_quality", "decode_to_yuv_planes"},
    )
}


class TypeHintRemover(ast._Unparser):  # type: ignore
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
