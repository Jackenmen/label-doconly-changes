from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Literal,
    Protocol,
    TypedDict,
    runtime_checkable,
)

import pathspec

if TYPE_CHECKING:
    from .app import App


MessageType = Literal["fail", "success", "error", "info"]


class FileInfoDict(TypedDict):
    filename: str
    contents_before: str | None
    contents_after: str | None


class HookInputDict(TypedDict):
    files: list[FileInfoDict]
    options: dict[str, str]
    app_options: dict[str, str]


class MessageDict(TypedDict):
    type: MessageType
    filename: str
    text: str


class HookOutputDict(TypedDict):
    errored: bool
    is_doc_only: bool
    messages: list[MessageDict]


def _get_file_from_ref(*, ref: str, filename: str) -> str | None:
    try:
        # this can't use `check_output()`'s encoding or text kwarg
        # instead of `.decode("utf-8")` because that forces universal newline behavior
        return subprocess.check_output(
            ("git", "cat-file", "blob", f"{ref}:{filename}"),
            stderr=subprocess.PIPE,
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        prefixes = tuple(
            f"fatal: path '{filename}' {error_msg} '".encode()
            for error_msg in (
                "exists on disk, but not in",
                "exists, but not",
                "does not exist in",
            )
        )
        if e.stderr.startswith(prefixes):
            return None
        raise


class FileInfo:
    __slots__ = ("filename", "contents_before", "contents_after")

    def __init__(
        self, filename: str, contents_before: str | None, contents_after: str | None
    ) -> None:
        self.filename = filename
        self.contents_before = contents_before
        self.contents_after = contents_after

    @classmethod
    def from_filename(cls, filename: str, *, base_ref: str) -> FileInfo:
        contents_before = _get_file_from_ref(ref=base_ref, filename=filename)
        contents_after = _get_file_from_ref(ref="HEAD", filename=filename)

        return cls(filename, contents_before, contents_after)

    def to_json(self) -> FileInfoDict:
        return {
            "filename": self.filename,
            "contents_before": self.contents_before,
            "contents_after": self.contents_after,
        }


class HookOutput:
    __slots__ = ("errored", "is_doc_only", "messages")

    def __init__(self) -> None:
        self.errored = False
        self.is_doc_only = True
        self.messages = []

    def _add_message(self, msg_type: MessageType, filename: str, text: str) -> None:
        self.messages.append(
            {
                "type": msg_type,
                "filename": filename,
                "text": text,
            }
        )

    def fail(self, filename: str, text: str) -> None:
        self.is_doc_only = False
        self._add_message("fail", filename, text)

    def success(self, filename: str, text: str) -> None:
        self._add_message("success", filename, text)

    def error(self, filename: str, text: str) -> None:
        self.errored = True
        self.is_doc_only = False
        self._add_message("error", filename, text)

    def info(self, filename: str, text: str) -> None:
        self._add_message("info", filename, text)

    def to_json(self) -> HookOutputDict:
        return {
            "errored": self.errored,
            "is_doc_only": self.is_doc_only,
            "messages": self.messages,
        }


class Hook:
    HOOKS_DIR = os.path.join(os.path.dirname(__file__), "hooks")

    def __init__(
        self,
        module_name: str,
        subhook_name: str = "",
        *,
        file_patterns: tuple[str, ...],
    ) -> None:
        *_, self.name = module_name.rpartition(".")
        if subhook_name:
            self.name += f".{subhook_name}"
        self.set_file_patterns(file_patterns)

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def set_file_patterns(self, file_patterns: Iterable[str]) -> None:
        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", file_patterns)

    def get_hook_input(self, app: App, file_data: list[FileInfo]) -> HookInputDict:
        return {
            "files": [file_info.to_json() for file_info in file_data],
            "options": app.hook_options[self.name],
            "app_options": app.options,
        }

    def run(self, app: App, file_data: list[FileInfo]) -> HookOutputDict:
        raise NotImplementedError


class SubprocessHook(Hook):
    def __init__(
        self,
        module_name: str,
        subhook_name: str = "",
        *,
        file_patterns: tuple[str, ...],
        script_name: str,
    ) -> None:
        super().__init__(module_name, subhook_name, file_patterns=file_patterns)
        self.script_name = os.path.join(self.HOOKS_DIR, "scripts", script_name)

    def __eq__(self, other: Any) -> bool:
        if (ret := super().__eq__(other)) is not True:
            return ret
        return self.script_name == other.script_name

    def __hash__(self) -> int:
        return hash((self.name, self.script_name))

    def run(self, app: App, file_data: list[FileInfo]) -> HookOutputDict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            executable_name = app.hook_options[self.name]["executable"]
            hook_input = self.get_hook_input(app, file_data)

            with open(os.path.join(tmp_dir, "input.json"), "w", encoding="utf-8") as fp:
                json.dump(hook_input, fp, separators=(",", ":"))

            subprocess.run((executable_name, self.script_name, tmp_dir), check=True)

            with open(os.path.join(tmp_dir, "output.json"), encoding="utf-8") as fp:
                return json.load(fp)


@runtime_checkable
class HookModule(Protocol):
    __name__: str
    AVAILABLE_HOOKS: list[Hook]


def get_hook_by_name(module: HookModule, name: str) -> Hook:
    try:
        return next(hook for hook in module.AVAILABLE_HOOKS if hook.name == name)
    except StopIteration:
        raise KeyError(
            f"There's no hook named {name!r} in module {module.__name__!r}"
        ) from None
