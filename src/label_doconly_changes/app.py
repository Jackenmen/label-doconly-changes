from __future__ import annotations

import importlib
import os
import subprocess
import sys

from .base_hooks import FileInfo, get_hook_by_name


class App:
    def __init__(
        self,
        *,
        base_ref: str,
        options: dict[str, str] | None = None,
        hook_options: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.exit_code = 0
        self.base_ref = base_ref
        self.options: dict[str, str] = {
            "enabled_hooks": "unconditional,python",
            **(options or {}),
        }
        self.hook_options = hook_options or {}
        self.hooks = []

    @classmethod
    def from_environ(cls) -> App:
        app_options: dict[str, str] = {}
        hook_options: dict[str, dict[str, str]] = {}
        for key, value in os.environ.items():
            if key.startswith("LDC_"):
                if key.startswith("HOOK_", 4):
                    hook_name, _, option_name = key[9:].lower().partition("__")
                    options = hook_options.setdefault(hook_name, {})
                    options[option_name] = value
                else:
                    app_options[key[4:].lower()] = value

        return cls(
            base_ref=os.environ["GITHUB_BASE_REF"],
            options=app_options,
            hook_options=hook_options,
        )

    def load_hooks(self) -> None:
        for hook_name in self.options["enabled_hooks"].split(","):
            hook_name = hook_name.strip()
            mod_name, _, subhook_name = hook_name.partition(".")
            module = importlib.import_module(f"label_doconly_changes.hooks.{mod_name}")
            hook = get_hook_by_name(module, hook_name)
            allowed_files = self.hook_options.get(hook_name, {}).get("allowed_files")
            if allowed_files:
                hook.set_file_patterns(allowed_files.splitlines())
            self.hooks.append(hook)

    def info(self, filename: str, text: str) -> None:
        print(filename, text)

    def error(self, filename: str, text: str) -> None:
        self.exit_code = 1
        print("!!!", filename, text, file=sys.stderr)

    def run(self) -> int:
        files = subprocess.check_output(
            ("git", "diff", "--name-only", f"{self.base_ref}.."), encoding="utf-8"
        ).splitlines()

        self.load_hooks()
        to_run = {hook: [] for hook in self.hooks}

        for filename in files:
            for hook in self.hooks:
                if hook.spec.match_file(filename):
                    try:
                        info = FileInfo.from_filename(filename, base_ref=self.base_ref)
                    except FileNotFoundError as exc:
                        self.error(filename, str(exc))
                    else:
                        to_run[hook].append(info)
                    break
            else:
                self.error(filename, "is not documentation.")

        for hook, file_data in to_run.items():
            output = hook.run(self, file_data)
            for message in output["messages"]:
                filename = message["filename"]
                text = message["text"]
                if message["type"] == "error":
                    self.error(filename, text)
                else:
                    self.info(filename, text)

        return self.exit_code