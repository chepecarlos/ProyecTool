"""Comandos para gestionar proyectos en Notion."""

import typer
from rich import print as rprint

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("list")
def list_projects() -> None:
    """📋  Lista los proyectos en Notion."""
    rprint("[yellow]TODO:[/] Obtener proyectos desde Notion API")


@app.command("config")
def configure(
    token: str = typer.Option(..., "--token", "-t", help="Token de integración de Notion.", envvar="NOTION_TOKEN"),
    database_id: str = typer.Option(..., "--db", help="ID de la base de datos en Notion.", envvar="NOTION_DATABASE_ID"),
) -> None:
    """⚙️   Configura la conexión con Notion."""
    rprint(f"[yellow]TODO:[/] Guardar configuración de Notion (token: {token[:8]}...)")
