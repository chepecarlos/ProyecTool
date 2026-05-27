"""Comandos para gestionar Tareas."""

import typer
from rich import print as rprint

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("list")
def list_tareas() -> None:
    """📋  Lista todas las tareas."""
    rprint("[yellow]TODO:[/] Listar tareas")


@app.command("add")
def add_tarea(
    nombre: str = typer.Argument(..., help="Nombre de la tarea."),
) -> None:
    """➕  Agrega una nueva tarea."""
    rprint(f"[yellow]TODO:[/] Agregar tarea [bold]{nombre}[/]")


@app.command("remove")
def remove_tarea(
    nombre: str = typer.Argument(..., help="Nombre de la tarea a eliminar."),
) -> None:
    """🗑️   Elimina una tarea."""
    rprint(f"[yellow]TODO:[/] Eliminar tarea [bold]{nombre}[/]")
