# stencil

A small CLI that scaffolds new projects from templates you define in a YAML file. Each template can create files with placeholder content and optionally run a command afterwards (for example `uv sync` or `python -m venv .venv`).

## Requirements

- Python 3.12+
- [Click](https://click.palletsprojects.com/) and [PyYAML](https://pyyaml.org/)

```bash
pip install click pyyaml
# or
uv add click pyyaml
```

## Usage

```bash
stencil list                               # show available templates
stencil new uv myproj                      # create ./myproj from the "uv" template
stencil new pip myproj ~/code              # create ~/code/myproj
stencil new pip myproj . --pyver 3.12      # set the Python version token
```

Running from source:

```bash
python app.py new uv myproj
```

### Commands

| Command | Description |
|---|---|
| `new TEMPLATE [PROJECT_NAME] [PATH]` | Create a project from a template |
| `list` | List templates and their descriptions |

### Arguments and options for `new`

| Name | Default | Description |
|---|---|---|
| `TEMPLATE` | required | Top-level key in `templates.yaml` |
| `PROJECT_NAME` | folder name | Creates a subfolder with this name inside `PATH` |
| `PATH` | `.` | Where to create the project |
| `--pyver` | `3.13` | Value for the `__PY_VER__` token |

If `PROJECT_NAME` is omitted, the project is created directly in `PATH` and the folder's name is used as the project name.

## templates.yaml

`templates.yaml` must sit **next to the executable** (or next to `app.py` when running from source). Edit it any time, no rebuild needed.

Every top-level key is a template:

```yaml
pip:
  description: Custom template using python pip.
  command:
    - python
    - -m
    - venv
    - .venv
  files:
    - main.py
    - README.md
  data:
    main.py: |
      def main():
          print('Hello from __PROJ_NAME__!')

      if __name__ == '__main__':
          main()
    README.md: |
      # __PROJ_NAME__
```

| Key | Description |
|---|---|
| `description` | Shown by `stencil list` (optional) |
| `files` | Files to create, relative to the project folder. Subfolders are created automatically |
| `data` | File contents, keyed by filename. Files in `files` with no entry here are created empty |
| `command` | Command to run in the project folder after the files are written (optional) |

Use `|` block scalars for file contents so newlines and indentation are preserved exactly. Use spaces, not tabs, since YAML forbids tab indentation.

### Tokens

These placeholders are replaced in file contents and in `command`:

| Token | Replaced with |
|---|---|
| `__PROJ_NAME__` | The project name |
| `__PY_VER__` | The value of `--pyver` |

To add a token, add a member to the `Token` enum in `app.py` and a value for it in the `values` dict in `new`.

### Security note

Templates can run arbitrary commands, so only use `templates.yaml` files you wrote or trust.

## Building with Nuitka

```bash
uv run python -m nuitka --onefile --output-filename=stencil --include-package=yaml app.py
```

Notes:

- Build with the same Python environment that has `click` and `pyyaml` installed.
- Keep the default console mode. Do not use `--windows-console-mode=disable` for a CLI.
- Do not bundle `templates.yaml`. Copy it next to the built executable instead:

```
stencil.exe
templates.yaml
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'yaml'` in the built exe | Rebuild with `--include-package=yaml` using the right Python environment |
| No output and exit code 1 on Windows | Rebuild without `--windows-console-mode=disable` |
| `Unknown template` | Check the name against `stencil list` |
| `'uv' is not installed or not on PATH` | Install the tool the template's `command` uses |
| Template file not found | Put `templates.yaml` in the same folder as the executable |
