"""Comandos para gestionar Áreas."""

import typer
from rich import print as rprint

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("list")
def list_areas() -> None:
    """📋  Lista todas las áreas."""
    rprint("[yellow]TODO:[/] Listar áreas")


@app.command("add")
def add_area(
    nombre: str = typer.Argument(..., help="Nombre del área."),
) -> None:
    """➕  Agrega una nueva área."""
    rprint(f"[yellow]TODO:[/] Agregar área [bold]{nombre}[/]")


@app.command("remove")
def remove_area(
    nombre: str = typer.Argument(..., help="Nombre del área a eliminar."),
) -> None:
    """🗑️   Elimina un área."""
    rprint(f"[yellow]TODO:[/] Eliminar área [bold]{nombre}[/]")
