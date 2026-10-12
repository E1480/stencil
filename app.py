import subprocess
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import click
import yaml


def app_dir() -> Path:
    # Nuitka sets __compiled__ on every module when compiled
    if "__compiled__" in globals():
        return Path(sys.argv[0]).resolve().parent
    return Path(__file__).resolve().parent

TEMPLATES = app_dir() / "templates.yaml"


class Token(StrEnum):
    NAME = "__PROJ_NAME__"
    PYVER = "__PY_VER__"


def load_templates() -> dict[str, dict[str, Any]]:
    raw = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))
    return cast(dict[str, dict[str, Any]], raw)


def render(content: str, values: dict[Token, str]) -> str:
    for token, value in values.items():
        content = content.replace(token, value)
    return content


def write_files(root: Path, template: dict[str, Any], values: dict[Token, str]) -> None:
    contents: dict[str, str] = template.get("data") or {}
    for filename in template.get("files") or []:
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(contents.get(filename, ""), values), encoding="utf-8")
        click.echo(f"  created {filename}")

def run_command(root: Path, template: dict[str, Any], values: dict[Token, str]) -> None:
    raw = template.get("command")
    if not raw:
        return

    # A flat list of strings is a single command; wrap it
    commands = cast(list[list[str]], [raw] if isinstance(raw[0], str) else raw)

    for command in commands:
        command = [render(part, values) for part in command]
        click.echo(f"  running: {' '.join(command)}")
        try:
            subprocess.run(command, cwd=root, check=True)
        except FileNotFoundError:
            raise click.ClickException(f"'{command[0]}' is not installed or not on PATH")
        except subprocess.CalledProcessError as e:
            raise click.ClickException(
                f"'{' '.join(command)}' failed with exit code {e.returncode}"
            )

@click.group()
def app(): ...


@app.command()
@click.argument("template_name", metavar="TEMPLATE")
@click.argument("project_name", required=False)
@click.argument("path", default=".", type=click.Path(path_type=Path))
@click.option("--pyver", default="3.13", show_default=True, help="Python version.")
def new(template_name: str, project_name: str | None, path: Path, pyver: str):
    """Create a project from TEMPLATE (a top-level key in templates.yaml)."""
    templates = load_templates()
    if template_name not in templates:
        raise click.ClickException(
            f"Unknown template '{template_name}'. Available: {', '.join(templates)}"
        )
    template = templates[template_name]

    root = (path / project_name if project_name else path).resolve()
    root.mkdir(parents=True, exist_ok=True)

    values = {
        Token.NAME: project_name or root.name,
        Token.PYVER: pyver,
    }

    click.echo("Creating boilerplate project...")
    write_files(root, template, values)
    run_command(root, template, values)


@app.command("list")
def list_templates():
    """List available templates."""
    click.echo("\n")
    for name, template in load_templates().items():
        description = (template.get("description") or "").strip()
        click.echo(f"| {name:<5}{"|":<2}  {description}")
    click.echo("\n")

if __name__ == "__main__":
    app()
