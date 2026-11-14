from label_doconly_changes.app import RunContext
from label_doconly_changes.base_hooks import FileInfo
from label_doconly_changes.hooks import unconditional


def test_unconditional_hook_is_always_doc_only() -> None:
    file_info = FileInfo("example.rst", "before", "after")
    affected_files = [file_info]
    all_affected_files = [file_info]
    ctx = RunContext(None, all_affected_files)

    hook = unconditional.AVAILABLE_HOOKS[0]
    output = hook.run(ctx, affected_files)

    assert output["errored"] is False
    assert output["is_doc_only"] is True
    assert len(output["messages"]) == 1
    assert output["messages"][0]["type"] == "info"
    assert output["messages"][0]["filename"] == file_info.filename
