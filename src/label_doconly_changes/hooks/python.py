from __future__ import annotations

import dataclasses
import enum
import itertools
import os
from collections import deque
from collections.abc import Iterator, Sequence
from typing import Generic, Literal, NamedTuple, Self, TypeVar

import libcst as cst

from label_doconly_changes.app import App
from label_doconly_changes.base_hooks import FileInfo, Hook, HookOutput, HookOutputDict

os.environ["LIBCST_PARSER_TYPE"] = "native"

_DocstringTarget = cst.Module | cst.ClassDef | cst.FunctionDef
_NodeT = TypeVar("_NodeT", bound=cst.CSTNode)
_ExprParentT = TypeVar("_ExprParentT")
_ExprT = TypeVar("_ExprT")


class DocstringLocation(NamedTuple, Generic[_ExprParentT, _ExprT]):
    expr_parent: _ExprParentT
    expr: _ExprT


_DocstringLocation = (
    DocstringLocation[
        cst.BaseCompoundStatement | cst.BaseSuite | cst.SimpleStatementLine, cst.Expr
    ]
    | DocstringLocation[None, None]
)


class ContinueSentinel(enum.Enum):
    CONTINUE = enum.auto()


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
    def from_contents(cls, contents: str) -> Self:
        self = cls(cst.parse_module(contents))
        self.base_node.visit(self)
        return self

    @classmethod
    def from_node(cls, base_node: cst.CSTNode) -> Self:
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
        expr: cst.BaseSuite | cst.BaseStatement | cst.BaseSmallStatement
        if isinstance(body, Sequence):
            if not node.body:
                return DocstringLocation(None, None)
            expr = body[0]
        else:
            expr = body

        parent = expr
        while isinstance(expr, (cst.BaseSuite, cst.SimpleStatementLine)):
            if not expr.body:
                return DocstringLocation(None, None)
            parent = expr
            expr = expr.body[0]
        if not isinstance(expr, cst.Expr):
            return DocstringLocation(None, None)

        val = expr.value
        # If something is not a string, it can't be a docstring :)
        if not isinstance(val, (cst.SimpleString, cst.ConcatenatedString)):
            return DocstringLocation(None, None)
        # Concatenated string's evaluated value may be None
        # if some part of it is an f-string.
        if val.evaluated_value is None:
            return DocstringLocation(None, None)

        return DocstringLocation(parent, expr)


class NodeIterator(Iterator[cst.CSTNode]):
    def __init__(self, nodes: list[cst.CSTNode], *, name: str | None = None) -> None:
        self.name = name
        self.additional_nodes: deque[cst.CSTNode] = deque()
        self.current = -1
        self.nodes = nodes
        self.nodes_it = enumerate(nodes)

    def __repr__(self) -> str:
        return f"<NodeIterator {self.name!r} current={self.current!r}>"

    def __iter__(self) -> NodeIterator:
        return self

    def __next__(self) -> cst.CSTNode:
        if self.additional_nodes:
            return self.additional_nodes.popleft()
        self.current, node = next(self.nodes_it)
        return node


class ModuleTracker:
    def __init__(self, contents: str, *, name: Literal["before", "after"]) -> None:
        self.extractor = DocstringExtractor.from_contents(contents)
        self.it = NodeIterator(self.extractor.nodes, name=name)
        self.loc: _DocstringLocation = DocstringLocation(None, None)

    @property
    def has_docstring(self) -> bool:
        return self.loc[0] is not None


class PythonAnalyzer:
    def __init__(self, contents_before: str, contents_after: str) -> None:
        self.before = ModuleTracker(contents_before, name="before")
        self.after = ModuleTracker(contents_after, name="after")
        self.it = itertools.zip_longest(self.before.it, self.after.it)
        #: Count of the docstring expressions in the currently tracked docstring target.
        #: 0 means that there's no currently tracked docstring target (which can mean
        #: that the target we tried to track didn't have docstrings or that we were
        #: simply not tracking anything).
        self.expr_count = 0
        #: Determines if the next single comparison should be skipped.
        self.skip_compare = False

    def is_docstring_only(self) -> bool:
        for b, a in self.it:
            # The zipped iterators should both end at the same time.
            if b is None or a is None:
                return False

            if (ret := self._handle_docstring_addition_and_removal(b, a)) is False:
                return False
            if ret is ContinueSentinel.CONTINUE:
                continue

            if self.skip_compare:
                self.skip_compare = False
            elif not shallow_equals(b, a):
                return False

            # If both docstring targets have a docstring, we don't want to compare their
            # contents so we set skip_compare when we see the docstring's Expr node.
            if self.expr_count == 2 and b is self.before.loc.expr:
                self.expr_count = 0
                self.skip_compare = True
                continue

            self._handle_docstring_target_node(b, a)

        return True

    def _handle_docstring_addition_and_removal(
        self, b: cst.CSTNode, a: cst.CSTNode
    ) -> bool | ContinueSentinel:
        if self.expr_count != 1:
            return True

        # Consume the docstring and everything until first non-whitespace
        # in the iterator that has a docstring.
        if b is self.before.loc.expr_parent:
            # b is not None so transitively, expr_parent can't be None either
            assert self.before.loc.expr_parent is not None
            b = self._consume_docstring_with_whitespace(
                self.before.it, self.before.loc.expr
            )
        elif a is self.after.loc.expr_parent:
            assert self.after.loc.expr_parent is not None
            a = self._consume_docstring_with_whitespace(
                self.after.it, self.after.loc.expr
            )
        else:
            return True
        self.expr_count = 0

        # Now that we're done with that, we still need to consume the whitespace which
        # may appear in the header/leading_lines of the nearest statement
        # as the iterator yields that statement *before* that whitespace and so
        # it wasn't consumed by the call before. This time we also want to consume
        # whitespace that appears in the iterator that didn't have a docstring.

        # Find the nearest statement, while checking that all encountered nodes
        # are equal. This is a simplified version of the main loop.
        self.before.it.additional_nodes.appendleft(b)
        self.after.it.additional_nodes.appendleft(a)
        for b, a in self.it:
            if b is None or a is None:
                return False
            if not shallow_equals(b, a):
                return False
            if isinstance(b, (cst.SimpleStatementLine, cst.BaseCompoundStatement)):
                break
        else:
            raise RuntimeError("Couldn't find a statement node.")

        self._consume_leading_lines(b, self.before.it)
        # b and a must have same types here due to earlier shallow_equals() call
        self._consume_leading_lines(a, self.after.it)  # type: ignore

        return ContinueSentinel.CONTINUE

    def _handle_docstring_target_node(self, b: _NodeT, a: _NodeT) -> Literal[False]:
        valid_classes = (cst.Module, cst.ClassDef, cst.FunctionDef)
        if type(b) in valid_classes:
            assert isinstance(a, valid_classes)
            assert isinstance(b, valid_classes)
            self.before.loc = self.before.extractor.doc_locations[b]
            self.after.loc = self.after.extractor.doc_locations[a]
            self.expr_count = self.before.has_docstring + self.after.has_docstring

            # If node is a module, we need to handle potential Comment nodes
            # in the module's header as they appear before the docstring and
            # we don't want to consume them in _handle_docstring_addition_and_removal().
            if self.expr_count == 1 and type(b) is cst.Module:
                if self.before.loc.expr_parent is None:
                    self._consume_leading_lines(b, self.before.it)
                else:
                    self._consume_leading_lines(a, self.after.it)

        return False

    @staticmethod
    def _consume_docstring_with_whitespace(
        nodes: NodeIterator, expr: cst.Expr
    ) -> cst.CSTNode:
        """
        Consume the passed docstring expression (including its whole string)
        and the whitespace surrounding it.

        Comments are added to the iterator's additional nodes instead of being consumed.
        """
        node = None
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
            break
        else:
            if skip_until is not None:
                raise RuntimeError("Couldn't find the `skip_until` node.")
            assert node is not None

        nodes.additional_nodes.extend(additional_nodes)
        return node

    @staticmethod
    def _consume_leading_lines(
        statement: cst.Module | cst.SimpleStatementLine | cst.BaseCompoundStatement,
        iterator: NodeIterator,
    ) -> None:
        """
        Consume passed statement's leading lines from the iterator, excluding comments
        (which are added to iterator's additional nodes).

        If the passed `statement` is a Module node, `header` attribute is used
        instead of `leading_lines`.
        """
        if isinstance(statement, cst.Module):
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
                hook_output.fail(file_info.filename, str(exc))
            else:
                # TODO: run AST check (on a tree with stripped docstrings)
                # for additional safety
                if analyzer.is_docstring_only():
                    hook_output.success(
                        file_info.filename, "contains only docstring changes."
                    )
                else:
                    hook_output.fail(
                        file_info.filename, "contains non-docstring changes."
                    )

        return hook_output.to_json()


AVAILABLE_HOOKS = [PythonHook(__name__, file_patterns=("*.py",))]
