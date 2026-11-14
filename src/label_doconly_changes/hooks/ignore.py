from label_doconly_changes.app import RunContext
from label_doconly_changes.base_hooks import FileInfo, Hook, HookOutputDict


class IgnoreHook(Hook):
    def run(self, ctx: RunContext, file_data: list[FileInfo]) -> HookOutputDict:
        other_files = [
            file_info
            for file_info in ctx.all_affected_files
            if file_info not in file_data
        ]
        return {
            "errored": False,
            "is_doc_only": bool(other_files),
            "messages": [
                {
                    "type": "info",
                    "filename": file_info.filename,
                    "text": "is ignored.",
                }
                for file_info in file_data
            ],
        }


AVAILABLE_HOOKS = [IgnoreHook(__name__, file_patterns=())]
