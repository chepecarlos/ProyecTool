"""Punto de entrada principal de proyectool."""

import typer
from rich import print as rprint
from rich.panel import Panel

from proyectool import __version__
from proyectool.commands import local, notion, sync

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(
    name="proyectool",
    help="🗂️  Sincroniza tus proyectos locales con Notion.",
    no_args_is_help=True,
    rich_markup_mode="markdown",
    context_settings=HELP_SETTINGS,
)

# Registrar sub-comandos
app.add_typer(local.app,  name="local",  help="📁  Gestiona proyectos locales.")
app.add_typer(notion.app, name="notion", help="📓  Gestiona proyectos en Notion.")
app.add_typer(sync.app,   name="sync",   help="🔄  Sincroniza local ↔ Notion.")


def _version_callback(value: bool) -> None:
    if value:
        rprint(Panel(f"[bold cyan]proyectool[/] v{__version__}", expand=False))
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version", "-v",
        callback=_version_callback,
        is_eager=True,
        help="Muestra la versión.",
    ),
) -> None:
    """proyectool — sincroniza tus proyectos locales con Notion."""
