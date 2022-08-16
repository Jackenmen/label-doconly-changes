from label_doconly_changes.base_hooks import SubprocessHook

AVAILABLE_HOOKS = [
    SubprocessHook(__name__, file_patterns=["*.py"], script_name="python.py"),
]
