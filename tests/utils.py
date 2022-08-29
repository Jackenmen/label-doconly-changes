from pathlib import Path
from typing import Iterator

HOOK_TEST_DATA = Path(__file__).parent.absolute() / "data/hooks"


def get_hook_test_data(*filenames: str) -> list[tuple[str, str]]:
    file_data = []
    for filename in filenames:
        with open(HOOK_TEST_DATA / filename, encoding="utf-8") as fp:
            contents = fp.read()

        it = iter(contents.splitlines(True))
        for line in it:
            if line.startswith("# --- BEFORE"):
                file_data.append(_read_test_file(it))

    return file_data


def _read_test_file(lines: Iterator[str]) -> tuple[str, str]:
    after_found = False
    before_lines = []
    after_lines = []

    for line in lines:
        if not after_found:
            if line.startswith("# --- AFTER"):
                after_found = True
            else:
                before_lines.append(line)
        else:
            if line.startswith("# ==="):
                break
            after_lines.append(line)
    else:
        if after_found:
            raise RuntimeError("Did not find the end of AFTER section")
        raise RuntimeError("Did not find the end of BEFORE section")

    # remove last new line to allow files not ending with an empty line
    before_lines[-1] = before_lines[-1][:-1]
    after_lines[-1] = after_lines[-1][:-1]

    return "".join(before_lines), "".join(after_lines)
