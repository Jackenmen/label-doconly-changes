import os
from collections.abc import Sequence

import libcst as cst

from label_doconly_changes.app import App
from label_doconly_changes.base_hooks import FileInfo, Hook, HookOutput, HookOutputDict

os.environ["LIBCST_PARSER_TYPE"] = "native"


class DocstringRemover(cst.CSTTransformer):
    def strip_docstring(
        self, updated_node: cst.Module | cst.ClassDef | cst.FunctionDef
    ) -> cst.CSTNode:
        body = updated_node.body
        if isinstance(body, Sequence):
            if not updated_node.body:
                return updated_node
            expr = body[0]
        else:
            expr = body

        while isinstance(expr, (cst.BaseSuite, cst.SimpleStatementLine)):
            if not expr.body:
                return updated_node
            expr = expr.body[0]
        if not isinstance(expr, cst.Expr):
            return updated_node

        val = expr.value
        # if something is not a string, it can't be a docstring :)
        if not isinstance(val, (cst.SimpleString, cst.ConcatenatedString)):
            return updated_node
        # concatenated string may be None if some part of it is an f-string
        if val.evaluated_value is None:
            return updated_node

        return updated_node.deep_remove(expr)

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.CSTNode:
        return self.strip_docstring(updated_node)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:
        return self.strip_docstring(updated_node)

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        return self.strip_docstring(updated_node)


class PythonHook(Hook):
    TRANSFORMER = DocstringRemover()

    @classmethod
    def parse(cls, contents: str) -> cst.Module:
        return cst.parse_module(contents).visit(cls.TRANSFORMER)

    def run(self, app: App, file_data: list[FileInfo]) -> HookOutputDict:
        hook_output = HookOutput()
        for file_info in file_data:
            try:
                before = self.parse(file_info.contents_before)
                after = self.parse(file_info.contents_after)
            except cst.ParserSyntaxError as exc:
                hook_output.error(file_info.filename, str(exc))
            else:
                if before.deep_equals(after):
                    hook_output.info(
                        file_info.filename, "contains only docstring changes."
                    )
                else:
                    hook_output.error(
                        file_info.filename, "contains non-docstring changes."
                    )

        return hook_output.to_json()


AVAILABLE_HOOKS = [PythonHook(__name__, file_patterns=["*.py"])]
