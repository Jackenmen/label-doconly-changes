import pytest

from label_doconly_changes.hooks import python
from tests.utils import get_hook_test_data


@pytest.mark.parametrize(
    "contents_before,contents_after", get_hook_test_data("python/is_doc_only_true.py")
)
def test_is_doc_only_true(contents_before: str, contents_after: str) -> None:
    print("--- BEFORE ---")
    print(contents_before)
    print("--- AFTER ----")
    print(contents_after)
    print("--------------")

    analyzer = python.PythonAnalyzer(contents_before, contents_after)
    assert analyzer.is_docstring_only()


@pytest.mark.parametrize(
    "contents_before,contents_after", get_hook_test_data("python/is_doc_only_false.py")
)
def test_is_doc_only_false(contents_before: str, contents_after: str) -> None:
    print("--- BEFORE ---")
    print(contents_before)
    print("--- AFTER ----")
    print(contents_after)
    print("--------------")

    analyzer = python.PythonAnalyzer(contents_before, contents_after)
    assert not analyzer.is_docstring_only()
