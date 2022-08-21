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

    before = python.PythonHook.parse(contents_before)
    after = python.PythonHook.parse(contents_after)
    try:
        assert before.deep_equals(after)
    except AssertionError:
        assert repr(before) == repr(after)
        raise


@pytest.mark.parametrize(
    "contents_before,contents_after", get_hook_test_data("python/is_doc_only_false.py")
)
def test_is_doc_only_false(contents_before: str, contents_after: str) -> None:
    print("--- BEFORE ---")
    print(contents_before)
    print("--- AFTER ----")
    print(contents_after)
    print("--------------")

    before = python.PythonHook.parse(contents_before)
    after = python.PythonHook.parse(contents_after)
    try:
        assert not before.deep_equals(after)
    except AssertionError:
        assert repr(before) != repr(after)
        raise
