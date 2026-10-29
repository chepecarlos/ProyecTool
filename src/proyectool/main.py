"""Punto de entrada principal de proyectool."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.panel import Panel

from proyectool import __version__
from proyectool.commands import area, local, notion, plantilla, proyecto, sync, tarea

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(
    name="proyectool",
    help="🗂️  Sincroniza tus proyectos locales con Notion.",
    no_args_is_help=True,
    rich_markup_mode="markdown",
    context_settings=HELP_SETTINGS,
)

# Registrar sub-comandos
app.add_typer(proyecto.app, name="proyecto", help="🗂️   Gestiona Proyectos.")
app.add_typer(tarea.app,    name="tarea",    help="✅  Gestiona Tareas.")
app.add_typer(area.app,     name="area",     help="🏷️   Gestiona Áreas.")
app.add_typer(notion.app,   name="notion",   help="📓  Configuración de Notion.")
app.add_typer(sync.app,     name="sync",     help="🔄  Sincroniza local ↔ Notion.")
app.add_typer(local.app,    name="local",    help="📁  Gestiona proyectos locales.")
app.add_typer(plantilla.app, name="plantilla", help="📐  Gestiona plantillas de proyectos.")


@app.command("open")
def open_en_navegador() -> None:
    """🌐  Abre el área o proyecto del folder actual en el navegador."""
    proyecto_file = Path.cwd() / ".proyectool" / "proyecto.md"
    area_file = Path.cwd() / ".proyectool" / "area.md"

    if proyecto_file.exists():
        proyecto.open_proyecto()
    elif area_file.exists():
        area.open_area()
    else:
        rprint("[yellow]⚠[/]  Este folder no tiene área ni proyecto configurado.")
        rprint("  Para crear un proyecto: [cyan]proyectool proyecto add <url>[/]")
        rprint("  Para configurar un área: [cyan]proyectool area add <url>[/]")


@app.command("info")
def info() -> None:
    """📊  Muestra info del área o proyecto del folder actual."""
    proyecto_file = Path.cwd() / ".proyectool" / "proyecto.md"
    area_file = Path.cwd() / ".proyectool" / "area.md"

    if proyecto_file.exists():
        proyecto.info_proyecto()
    elif area_file.exists():
        area.info_area()
    else:
        rprint("[yellow]⚠[/]  Este folder no tiene área ni proyecto configurado.")
        rprint("  Para crear un proyecto: [cyan]proyectool proyecto add <url>[/]")
        rprint("  Para configurar un área: [cyan]proyectool area add <url>[/]")


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
