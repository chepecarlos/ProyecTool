"""Comandos para gestionar proyectos en Notion."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.table import Table
from rich.console import Console

from proyectool.miLibrerias.FuncionesArchivos import ObtenerArchivo, SalvarValor

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

console = Console()

# Ruta donde se guarda la configuración de Notion
CONFIG_DIR  = Path.home() / ".config" / "proyectool"
CONFIG_FILE = CONFIG_DIR / "notion.md"

# Campos requeridos y su descripción amigable
CAMPOS = {
    "token":        "Token de integración de Notion",
    "db_proyectos": "Base de datos de Proyectos",
    "db_area":      "Base de datos de Áreas",
}


def _obtener_config() -> dict:
    """Lee la configuración guardada de Notion."""
    data = ObtenerArchivo(str(CONFIG_FILE), EnConfig=False)
    return data or {}


def _mostrar_estado(config: dict) -> bool:
    """Muestra tabla de estado. Devuelve True si todo está configurado."""
    table = Table(title="Configuración Notion", highlight=True)
    table.add_column("Campo",       style="cyan",  no_wrap=True)
    table.add_column("Estado",      justify="center")
    table.add_column("Valor",       style="dim")

    completo = True
    for campo, descripcion in CAMPOS.items():
        valor = config.get(campo)
        if valor:
            estado = "[green]✓[/]"
            # Ocultar parte del token por seguridad
            mostrar = f"{valor[:8]}..." if campo == "token" else valor
        else:
            estado = "[red]✗ falta[/]"
            mostrar = f"[yellow]proyectool notion config --{campo.replace('_', '-')} <valor>[/]"
            completo = False
        table.add_row(descripcion, estado, mostrar)

    rprint(table)
    rprint(f"[dim]Archivo: {CONFIG_FILE}[/]\n")
    return completo


@app.command("config")
def configure(
    token: str = typer.Option(
        None, "--token", "-t",
        help="Token de integración de Notion.",
        envvar="NOTION_TOKEN",
    ),
    db_proyectos: str = typer.Option(
        None, "--db-proyectos",
        help="ID de la base de datos de Proyectos en Notion.",
    ),
    db_area: str = typer.Option(
        None, "--db-area",
        help="ID de la base de datos de Áreas en Notion.",
    ),
) -> None:
    """⚙️   Guarda la configuración de conexión con Notion."""

    if not any([token, db_proyectos, db_area]):
        # Sin argumentos → mostrar estado actual
        config = _obtener_config()
        completo = _mostrar_estado(config)
        if not completo:
            rprint("[yellow]⚠[/]  Hay campos sin configurar.")
        raise typer.Exit()

    # Guardar cada valor recibido
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if token:
        SalvarValor(str(CONFIG_FILE), "token", token, local=False)
        rprint(f"[green]✓[/] token guardado")

    if db_proyectos:
        SalvarValor(str(CONFIG_FILE), "db_proyectos", db_proyectos, local=False)
        rprint(f"[green]✓[/] db_proyectos guardado")

    if db_area:
        SalvarValor(str(CONFIG_FILE), "db_area", db_area, local=False)
        rprint(f"[green]✓[/] db_area guardado")

    # Mostrar estado actualizado
    rprint()
    config = _obtener_config()
    _mostrar_estado(config)


@app.command("list")
def list_projects() -> None:
    """📋  Lista los proyectos en Notion."""
    rprint("[yellow]TODO:[/] Obtener proyectos desde Notion API")
