from textwrap import dedent

import pytest

from label_doconly_changes.hooks import python


@pytest.mark.parametrize(
    "contents_before,contents_after,is_doc_only",
    (
        # identical contents
        ("x = 1", "x = 1", True),
        (
            '''\
            """module docstring"""
            x = 1
            ''',
            '''\
            """module docstring"""
            x = 1
            ''',
            True,
        ),
        # modified variable value
        ("x = 1", "x = 2", False),
        (
            '''\
            """module docstring"""
            x = 1
            ''',
            '''\
            """module docstring"""
            x = 2
            ''',
            False,
        ),
        # modified docstring
        (
            '''\
            """module docstring"""
            x = 1
            ''',
            '''\
            """changed docstring"""
            x = 1
            ''',
            True,
        ),
        # modified docstring *and* variable value
        (
            '''\
            """module docstring"""
            x = 1
            ''',
            '''\
            """changed docstring"""
            x = 2
            ''',
            False,
        ),
        # removal of a docstring
        (
            '''\
            """module docstring"""
            x = 1
            ''',
            """\
            x = 1
            """,
            True,
        ),
    ),
)
def test_docstring_removal(
    contents_before: str,
    contents_after: str,
    is_doc_only: bool,
) -> None:
    contents_before = dedent(contents_before)
    contents_after = dedent(contents_after)
    print("--- BEFORE ---")
    print(contents_before)
    print("--- AFTER ----")
    print(contents_after)
    print("--------------")

    before = python.PythonHook.parse(contents_before)
    after = python.PythonHook.parse(contents_after)
    if is_doc_only:
        try:
            assert before.deep_equals(after)
        except AssertionError:
            assert repr(before) == repr(after)
            raise
    else:
        try:
            assert not before.deep_equals(after)
        except AssertionError:
            assert repr(before) != repr(after)
            raise
