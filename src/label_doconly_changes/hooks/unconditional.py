from label_doconly_changes.app import App
from label_doconly_changes.base_hooks import FileInfo, Hook, HookOutputDict


class UnconditionalHook(Hook):
    def run(self, app: App, file_data: list[FileInfo]) -> HookOutputDict:
        return {
            "errored": False,
            "is_doc_only": True,
            "messages": [
                {
                    "type": "info",
                    "filename": file_info.filename,
                    "text": "is documentation.",
                }
                for file_info in file_data
            ],
        }


AVAILABLE_HOOKS = [UnconditionalHook(__name__, file_patterns=("*.rst", "*.md"))]
