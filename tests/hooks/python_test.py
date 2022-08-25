import libcst as cst
import pytest

from label_doconly_changes.hooks import python
from tests.utils import get_hook_test_data


class _ListSimplifier(cst.CSTTransformer):
    def __init__(self, *, max_depth: int = 1) -> None:
        self.depth = 0
        self.max_depth = max_depth

    def visit_List(self, original_node: cst.CSTNode) -> bool:
        self.depth += 1
        return True

    def leave_List(
        self, original_node: cst.List, updated_node: cst.List
    ) -> cst.CSTNode:
        self.depth -= 1
        if self.depth >= self.max_depth:
            return updated_node.with_changes(
                elements=[cst.Element(cst.Ellipsis())],
                lbracket=cst.LeftSquareBracket(),
                rbracket=cst.RightSquareBracket(),
            )
        return updated_node


def simplify_list(nodes: list[cst.CSTNode], *, max_depth: int = 1) -> str:
    visitor = _ListSimplifier(max_depth=max_depth)
    return cst.parse_module(repr(nodes)).visit(visitor).code


def print_extractor_info(extractor: python.DocstringExtractor) -> None:
    print("+ contents:")
    print(extractor.base_node.code)
    print("+ module node:")
    print(extractor.base_node)
    print("+ node traverse order:")
    print(simplify_list(extractor.nodes[1:]))


def print_analyzer_info(analyzer: python.PythonAnalyzer) -> None:
    print("--- BEFORE ---")
    print_extractor_info(analyzer.before)
    print("--- AFTER ----")
    print_extractor_info(analyzer.after)
    print("--------------")


@pytest.mark.parametrize(
    "contents_before,contents_after", get_hook_test_data("python/is_doc_only_true.py")
)
def test_is_doc_only_true(contents_before: str, contents_after: str) -> None:
    analyzer = python.PythonAnalyzer(contents_before, contents_after)
    try:
        assert analyzer.is_docstring_only()
    except Exception:
        print_analyzer_info(analyzer)
        raise


@pytest.mark.parametrize(
    "contents_before,contents_after", get_hook_test_data("python/is_doc_only_false.py")
)
def test_is_doc_only_false(contents_before: str, contents_after: str) -> None:
    analyzer = python.PythonAnalyzer(contents_before, contents_after)
    try:
        assert not analyzer.is_docstring_only()
    except Exception:
        print_analyzer_info(analyzer)
        raise
