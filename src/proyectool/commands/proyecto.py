"""Comandos para gestionar Proyectos."""

import typer
from rich import print as rprint

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("list")
def list_proyectos() -> None:
    """📋  Lista todos los proyectos."""
    rprint("[yellow]TODO:[/] Listar proyectos")


@app.command("add")
def add_proyecto(
    nombre: str = typer.Argument(..., help="Nombre del proyecto."),
) -> None:
    """➕  Agrega un nuevo proyecto."""
    rprint(f"[yellow]TODO:[/] Agregar proyecto [bold]{nombre}[/]")


@app.command("remove")
def remove_proyecto(
    nombre: str = typer.Argument(..., help="Nombre del proyecto a eliminar."),
) -> None:
    """🗑️   Elimina un proyecto."""
    rprint(f"[yellow]TODO:[/] Eliminar proyecto [bold]{nombre}[/]")
