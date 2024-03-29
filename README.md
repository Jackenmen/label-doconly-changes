# label-doconly-changes

[![Sponsor on GitHub](https://img.shields.io/github/sponsors/Jackenmen?logo=github)](https://github.com/sponsors/Jackenmen)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://user-images.githubusercontent.com/6032823/111363465-600fe880-8690-11eb-8377-ec1d4d5ff981.png)](https://github.com/PyCQA/isort)
[![We use pre-commit!](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> GitHub action for labelling and unlabelling PRs based on whether they contain
> only documentation changes.
>
> Supports file patterns and Python docstrings.

## Basic usage

Create a YAML file in `.github/workflows` directory of your repository,
e.g. `.github/workflows/label_doconly_changes.yaml` with content:

```yaml
name: Label the PR if it only contains documentation changes.
on:
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  pull-requests: write

jobs:
  label_doconly_changes:
    runs-on: ubuntu-latest
    steps:
      - name: Label documentation-only changes.
        uses: Jackenmen/label-doconly-changes@v1
```

## Global options

`<HOOK_NAME>` should be replaced with UPPERCASE name of the hook.

### `LDC_ENABLED_HOOKS`

Comma-separated list of enabled hooks.

[Available hooks](#Available-hooks) can be found below.

Default value: `unconditional,python`

```yaml
- name: Label documentation-only changes.
  uses: Jackenmen/label-doconly-changes@v1
  env:
    LDC_ENABLED_HOOKS: unconditional
```

### `LDC_LABELS`

Comma-separated list of labels to apply to/remove from documentation-only pull requests.

Default value: `doc-only`

```yaml
- name: Label documentation-only changes.
  uses: Jackenmen/label-doconly-changes@v1
  env:
    LDC_LABELS: Documentation-only change,Non-code change
```

### `LDC_HOOK_<HOOK_NAME>__FILES`

Gitignore-style patterns ('wildmatch' patterns) for files that should be
handled by the `<HOOK_NAME>` hook. As opposed to .gitignore, these patterns
specify files that should be allowed, not disallowed.

The pattern format is explained here: https://git-scm.com/docs/gitignore

Default value is hook-specific.

```yaml
- name: Label documentation-only changes.
  uses: Jackenmen/label-doconly-changes@v1
  env:
    LDC_HOOK_UNCONDITIONAL__FILES: |-
      *.rst
      *.md
```

## Available hooks

### `unconditional`

Files handled by this hook are allowed to be in the PR unconditionally.

Default value of `LDC_HOOK_UNCONDTIONAL__FILES`:
```gitignore
*.rst
*.md
```

### `python`

Files handled by this hook are allowed to be in the PR *if* they're Python files
containing only docstring changes.

The parser used by this hook is [LibCST](https://github.com/Instagram/LibCST)
which supports parsing syntax of Python 3.0 and above.
Currently there is no way to choose the version that should be used by the parser.

Default value of `LDC_HOOK_PYTHON__FILES`:
```gitignore
*.py
```

## Examples

```yaml
name: Label the PR if it only contains documentation changes.
on:
  pull_request_target:
    types: [opened, synchronize, reopened, labeled, unlabeled]

permissions:
  pull-requests: write

label_doconly_changes:
  steps:
    - name: Label documentation-only changes.
      uses: Jackenmen/label-doconly-changes@v1
      env:
        # unconditionally label *.txt files if they're not `docs/prolog.txt`
        LDC_HOOK_UNCONDITIONAL__FILES: |-
          *.rst
          *.md
          *.txt
          !/docs/prolog.txt
        # disable `python` hook
        LDC_ENABLED_HOOKS: unconditional
```

## License

Distributed under the Apache License 2.0. See ``LICENSE`` for more information.

---

> Jakub Kuczys &nbsp;&middot;&nbsp;
> GitHub [@Jackenmen](https://github.com/Jackenmen)
