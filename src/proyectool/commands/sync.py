"""Comandos para sincronizar proyectos locales con Notion."""

import typer
from rich import print as rprint

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("run")
def sync_all(
    dry_run: bool = typer.Option(False, "--dry-run", help="Simula la sincronización sin hacer cambios."),
) -> None:
    """🔄  Sincroniza todos los proyectos locales con Notion."""
    modo = "[dim](modo simulación)[/]" if dry_run else ""
    rprint(f"[yellow]TODO:[/] Sincronizar local ↔ Notion {modo}")


@app.command("status")
def sync_status() -> None:
    """📊  Muestra el estado de sincronización de cada proyecto."""
    rprint("[yellow]TODO:[/] Mostrar diferencias entre local y Notion")
