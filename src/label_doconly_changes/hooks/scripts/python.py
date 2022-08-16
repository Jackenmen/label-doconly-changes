import json
import os
import sys
import tokenize
from io import StringIO
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    if sys.version_info >= (3, 8):
        from typing import Literal, TypedDict
    else:
        from typing_extensions import Literal, TypedDict

    class FileInfoDict(TypedDict):
        filename: str
        contents_before: str
        contents_after: str

    class HookInputDict(TypedDict):
        files: list[FileInfoDict]
        options: dict[str, str]
        app_options: dict[str, str]

    class MessageDict(TypedDict):
        type: Literal["error", "info"]
        filename: str
        text: str

    class HookOutputDict(TypedDict):
        is_doc_only: bool
        messages: list[MessageDict]

else:
    FileInfoDict = dict
    HookInputDict = dict
    MessageDict = dict
    HookOutputDict = dict


if sys.version_info >= (3, 7):
    FRESH_MODULE_TOKENS = (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING)
else:
    FRESH_MODULE_TOKENS = (tokenize.COMMENT, tokenize.NL)


def is_literal_string(s: str) -> bool:
    return s[0] in "'\"" or (s[0] in "rRuU" and s[1] in "'\"")


class _TokenEater:
    def __init__(self) -> None:
        self._state = self._waiting
        self._fresh_module = True
        self.tokens = []
        self._enclosure_count = 0
        self._docstring_token_count = 0

    def __call__(self, token: tokenize.TokenInfo) -> None:
        self.tokens.append(token)
        self._state(token)

    def _waiting(self, token: tokenize.TokenInfo) -> None:
        # module docstring?
        if self._fresh_module:
            if token.type == tokenize.STRING:
                self._fresh_module = False
                self.tokens.pop()
                return
            elif token.type in FRESH_MODULE_TOKENS:
                return
            self._fresh_module = False

        # class or func/method docstring?
        if token.type == tokenize.NAME and token.string in ("class", "def"):
            self._state = self._suite_seen
            return

    def _suite_seen(self, token: tokenize.TokenInfo) -> None:
        # skip over any enclosure pairs until we see the colon
        if token.type == tokenize.OP:
            if token.string == ":" and self._enclosure_count == 0:
                # we see a colon and we're not in an enclosure: end of def
                self._state = self._suite_docstring
            elif token.string in "([{":
                self._enclosure_count += 1
            elif token.string in ")]}":
                self._enclosure_count -= 1

    def _suite_docstring(self, token: tokenize.TokenInfo) -> None:
        # ignore any intervening noise
        if token.type == tokenize.STRING and is_literal_string(token.string):
            self._docstring_token_count = 1
            self._state = self._suite_seen_docstring
        elif token.type not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.COMMENT):
            # there was no class docstring
            self._state = self._waiting

    def _suite_seen_docstring(self, token: tokenize.TokenInfo) -> None:
        if token.type == tokenize.NEWLINE:
            del self.token[-self._docstring_token_count - 1 :]
            self._state = self._waiting
        elif (
            token.type == tokenize.STRING
            and is_literal_string(token.string)
            or token.type == tokenize.COMMENT
        ):
            self._docstring_token_count += 1
        else:
            # there was no class docstring
            self._state = self._waiting


def get_tokens(contents: bytes) -> List[tokenize.TokenInfo]:
    eater = _TokenEater()
    for token in tokenize.generate_tokens(StringIO(contents).readline):
        eater(token)
    return eater.tokens


class App:
    def __init__(self, control_dir: str) -> None:
        self.control_dir = control_dir
        self.is_doc_only = True
        self.messages: List[MessageDict] = []

    def info(self, filename: str, text: str) -> None:
        self.messages.append(
            {
                "type": "info",
                "filename": filename,
                "text": text,
            }
        )

    def error(self, filename: str, text: str) -> None:
        self.is_doc_only = False
        self.messages.append(
            {
                "type": "error",
                "filename": filename,
                "text": text,
            }
        )

    def check_file(self, file_info: FileInfoDict) -> None:
        try:
            before = get_tokens(file_info["contents_before"])
            after = get_tokens(file_info["contents_after"])
        except tokenize.TokenError as e:
            self.error(
                file_info["filename"],
                f"- {e.args[0]}: line {e.args[1][0]}, column {e.args[1][1]}",
            )
        else:
            if before == after:
                self.info(file_info["filename"], "contains only docstring changes.")
            else:
                self.error(file_info["filename"], "contains non-docstring changes.")

    def run(self) -> None:
        with open(os.path.join(self.control_dir, "input.json"), encoding="utf-8") as fp:
            hook_input: HookInputDict = json.load(fp)

        for file_info in hook_input["files"]:
            self.check_file(file_info)

        hook_output: HookOutputDict = {
            "is_doc_only": self.is_doc_only,
            "messages": [],
        }
        with open(
            os.path.join(self.control_dir, "output.json"), "w", encoding="utf-8"
        ) as fp:
            json.dump(hook_output, fp)


if __name__ == "__main__":
    App(sys.argv[1]).run()
