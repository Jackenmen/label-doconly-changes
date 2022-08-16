from textwrap import dedent

import pytest

from python import get_tokens


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
def test_get_tokens(
    contents_before: str, contents_after: str, is_doc_only: bool
) -> None:
    contents_before = dedent(contents_before)
    contents_after = dedent(contents_after)
    print("--- BEFORE ---")
    print(contents_before)
    print("--- AFTER ----")
    print(contents_after)
    print("--------------")

    before = get_tokens(contents_before)
    after = get_tokens(contents_after)

    if is_doc_only:
        assert before == after
    else:
        assert before != after
