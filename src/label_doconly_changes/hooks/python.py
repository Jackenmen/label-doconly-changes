from __future__ import annotations

import dataclasses
import itertools
import os
from collections import deque
from collections.abc import Iterator, Sequence
from typing import TypeVar

import libcst as cst

from label_doconly_changes.app import App
from label_doconly_changes.base_hooks import FileInfo, Hook, HookOutput, HookOutputDict

os.environ["LIBCST_PARSER_TYPE"] = "native"

_NodeListGeneratorT = TypeVar("_NodeListGeneratorT", bound="NodeListGenerator")
_DocstringTarget = cst.Module | cst.ClassDef | cst.FunctionDef
_DocstringLocation = (
    tuple[cst.BaseSuite | cst.SimpleStatementLine, cst.Expr] | tuple[None, None]
)


def shallow_equals(a: cst.CSTNode, b: cst.CSTNode) -> bool:
    if type(a) is not type(b):
        return False
    for field in (f for f in dataclasses.fields(a) if f.compare is True):
        a_value = getattr(a, field.name)
        b_value = getattr(b, field.name)
        if isinstance(a_value, cst.CSTNode) and isinstance(b_value, cst.CSTNode):
            # this is a shallow equality comparison
            continue
        if isinstance(a_value, Sequence) and isinstance(b_value, Sequence):
            if not (
                isinstance(a_value, (str, bytes)) or isinstance(b_value, (str, bytes))
            ):
                # this is a shallow equality comparison
                continue
        if a_value != b_value:
            return False
    return True


class NodeListGenerator(cst.CSTVisitor):
    def __init__(self, base_node: cst.CSTNode) -> None:
        self.base_node = base_node
        self.nodes: list[cst.CSTNode] = []

    def on_visit(self, node: cst.CSTNode) -> bool | None:
        self.nodes.append(node)
        return super().on_visit(node)

    @classmethod
    def from_contents(cls, contents: str) -> _NodeListGeneratorT:
        self = cls(cst.parse_module(contents))
        self.base_node.visit(self)
        return self

    @classmethod
    def from_node(cls, base_node: cst.CSTNode) -> _NodeListGeneratorT:
        self = cls(base_node)
        base_node.visit(self)
        return self


class DocstringExtractor(NodeListGenerator):
    def __init__(self, module: cst.Module) -> None:
        super().__init__(module)
        self.doc_locations: dict[_DocstringTarget, _DocstringLocation] = {}

    def visit_Module(self, node: cst.Module) -> None:
        self.doc_locations[node] = self.extract_docstring(node)

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self.doc_locations[node] = self.extract_docstring(node)

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.doc_locations[node] = self.extract_docstring(node)

    def extract_docstring(self, node: _DocstringTarget) -> _DocstringLocation:
        body = node.body
        if isinstance(body, Sequence):
            if not node.body:
                return (None, None)
            expr = body[0]
        else:
            expr = body

        parent = expr
        while isinstance(expr, (cst.BaseSuite, cst.SimpleStatementLine)):
            if not expr.body:
                return (None, None)
            parent = expr
            expr = expr.body[0]
        if not isinstance(expr, cst.Expr):
            return (None, None)

        val = expr.value
        # if something is not a string, it can't be a docstring :)
        if not isinstance(val, (cst.SimpleString, cst.ConcatenatedString)):
            return (None, None)
        # concatenated string may be None if some part of it is an f-string
        if val.evaluated_value is None:
            return (None, None)

        return (parent, expr)


class NodeIterator(Iterator[cst.CSTNode]):
    def __init__(self, nodes: list[cst.CSTNode]) -> None:
        self.name = None
        self.additional_nodes: deque[cst.CSTNode] = deque()
        self.current = -1
        self.nodes = nodes
        self.nodes_it = enumerate(nodes)

    def __repr__(self) -> None:
        return f"<NodeIterator {self.name!r} current={self.current!r}>"

    def __iter__(self) -> NodeIterator:
        return self

    def __next__(self) -> cst.CSTNode:
        if self.additional_nodes:
            return self.additional_nodes.popleft()
        self.current, node = next(self.nodes_it)
        return node


class PythonAnalyzer:
    def __init__(self, contents_before: str, contents_after: str) -> None:
        self.before = DocstringExtractor.from_contents(contents_before)
        self.after = DocstringExtractor.from_contents(contents_after)

    def is_docstring_only(self) -> bool:
        before_it = NodeIterator(self.before.nodes)
        after_it = NodeIterator(self.after.nodes)
        before_loc = after_loc = (None, None)
        expr_count = 0
        skip_compare = False
        it = itertools.zip_longest(before_it, after_it)
        for a, b in it:
            if a is None or b is None:
                return False

            if expr_count == 1 and (a is before_loc[0] or b is after_loc[0]):
                expr_count = 0
                if a is before_loc[0]:
                    a = self._consume_docstring_with_whitespace(
                        before_it, before_loc[1]
                    )
                else:
                    b = self._consume_docstring_with_whitespace(after_it, after_loc[1])
                before_it.additional_nodes.appendleft(a)
                after_it.additional_nodes.appendleft(b)
                for a, b in it:
                    if a is None or b is None:
                        return False
                    if not shallow_equals(a, b):
                        return False
                    if isinstance(a, cst.BaseStatement):
                        break
                self._consume_leading_lines(a, before_it)
                self._consume_leading_lines(b, after_it)
                continue

            if skip_compare:
                skip_compare = False
            elif not shallow_equals(a, b):
                return False

            if expr_count == 2 and a is before_loc[1]:
                expr_count = 0
                skip_compare = True
                continue

            node_type = type(a)
            if node_type in (cst.Module, cst.ClassDef, cst.FunctionDef):
                before_loc = self.before.doc_locations[a]
                after_loc = self.after.doc_locations[b]
                expr_count = 2 - (before_loc, after_loc).count((None, None))
                if expr_count == 1 and node_type is cst.Module:
                    if before_loc[0] is None:
                        self._consume_leading_lines(a, before_it)
                    else:
                        self._consume_leading_lines(b, after_it)

        return True

    @staticmethod
    def _consume_docstring_with_whitespace(
        nodes: NodeIterator, expr: cst.Expr
    ) -> cst.CSTNode:
        skip_until = None
        additional_nodes = []
        for node in nodes:
            if skip_until is not None:
                if node is skip_until:
                    skip_until = None
                continue
            if type(node) in (
                cst.TrailingWhitespace,
                cst.SimpleWhitespace,
                cst.Newline,
                # TODO: check if this needs to be here?
                cst.EmptyLine,
            ):
                continue
            if type(node) is cst.Comment:
                additional_nodes.append(node)
                continue
            if node is expr:
                skip_until = expr.value
                while isinstance(skip_until, cst.ConcatenatedString):
                    skip_until = skip_until.right
                continue
            nodes.additional_nodes.extend(additional_nodes)
            return node
        else:
            # TODO: figure out if this can happen in sth like:
            # class X:
            #     '''docstring'''
            # [END OF FILE]
            raise RuntimeError("Ran out of nodes?")

    @staticmethod
    def _consume_leading_lines(
        statement: cst.Module | cst.SimpleStatementLine | cst.BaseCompoundStatement,
        iterator: NodeIterator,
    ) -> None:
        if type(statement) is cst.Module:
            leading_lines = statement.header
        else:
            leading_lines = statement.leading_lines

        additional_nodes = []
        for base_node in leading_lines:
            for node in NodeListGenerator.from_node(base_node).nodes:
                if node is not next(iterator, None):
                    raise RuntimeError("Expected leading line is missing.")
                if type(node) is cst.Comment:
                    additional_nodes.append(node)
        iterator.additional_nodes.extend(additional_nodes)


class PythonHook(Hook):
    def run(self, app: App, file_data: list[FileInfo]) -> HookOutputDict:
        hook_output = HookOutput()
        for file_info in file_data:
            try:
                analyzer = PythonAnalyzer(
                    file_info.contents_before, file_info.contents_after
                )
            except cst.ParserSyntaxError as exc:
                hook_output.error(file_info.filename, str(exc))
            else:
                # TODO: run AST check (on a tree with stripped docstrings)
                # for additional safety
                if analyzer.is_docstring_only():
                    hook_output.info(
                        file_info.filename, "contains only docstring changes."
                    )
                else:
                    hook_output.error(
                        file_info.filename, "contains non-docstring changes."
                    )

        return hook_output.to_json()


AVAILABLE_HOOKS = [PythonHook(__name__, file_patterns=["*.py"])]
