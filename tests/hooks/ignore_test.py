from label_doconly_changes.app import RunContext
from label_doconly_changes.base_hooks import FileInfo
from label_doconly_changes.hooks import ignore


def test_ignore_hook_is_not_doc_only_when_no_other_files_are_present() -> None:
    file_info = FileInfo("example", "before", "after")
    affected_files = [file_info]
    all_affected_files = [file_info]
    ctx = RunContext(None, all_affected_files)

    hook = ignore.AVAILABLE_HOOKS[0]
    output = hook.run(ctx, affected_files)

    assert output["errored"] is False
    assert output["is_doc_only"] is False
    assert len(output["messages"]) == 1
    assert output["messages"][0]["type"] == "info"
    assert output["messages"][0]["filename"] == file_info.filename


def test_ignore_hook_is_doc_only_when_other_files_are_present() -> None:
    file_info = FileInfo("example", "before", "after")
    another_file_info = FileInfo("another_file", "before", "after")
    affected_files = [file_info]
    all_affected_files = [file_info, another_file_info]
    ctx = RunContext(None, all_affected_files)

    hook = ignore.AVAILABLE_HOOKS[0]
    output = hook.run(ctx, affected_files)

    assert output["errored"] is False
    assert output["is_doc_only"] is True
    assert len(output["messages"]) == 1
    assert output["messages"][0]["type"] == "info"
    assert output["messages"][0]["filename"] == file_info.filename
