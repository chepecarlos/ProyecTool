"""Comandos para gestionar proyectos locales."""

import typer
from rich import print as rprint
from rich.table import Table

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("list")
def list_projects(
    path: str = typer.Option(".", "--path", "-p", help="Directorio raíz donde buscar proyectos."),
) -> None:
    """📋  Lista todos los proyectos locales encontrados."""
    rprint(f"[yellow]TODO:[/] Listar proyectos en [cyan]{path}[/]")


@app.command("add")
def add_project(
    name: str = typer.Argument(..., help="Nombre del proyecto."),
    path: str = typer.Argument(".", help="Ruta del proyecto."),
) -> None:
    """➕  Registra un proyecto local en proyectool."""
    rprint(f"[yellow]TODO:[/] Agregar proyecto [bold]{name}[/] desde [cyan]{path}[/]")


@app.command("remove")
def remove_project(
    name: str = typer.Argument(..., help="Nombre del proyecto a eliminar."),
) -> None:
    """🗑️   Elimina un proyecto del registro local."""
    rprint(f"[yellow]TODO:[/] Eliminar proyecto [bold]{name}[/]")
