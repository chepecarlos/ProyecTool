"""Comandos para gestionar Áreas."""

from pathlib import Path

import typer
from rich import print as rprint

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

# Un solo archivo de área por folder
AREA_FILE = Path(".proyectool") / "area.md"


def _ruta_area() -> Path:
    return Path.cwd() / AREA_FILE


@app.command("list")
def list_areas() -> None:
    """📋  Muestra el área del folder actual."""
    archivo = _ruta_area()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay área configurada en este folder.")
        rprint(f"  Usa: [cyan]proyectool area add <url>[/]")
        return

    rprint(f"[cyan]url:[/] {data.get('url', '—')}")


@app.command("add")
def add_area(
    url: str = typer.Argument(..., help="URL del área en Notion."),
) -> None:
    """➕  Configura el área de este folder."""
    archivo = _ruta_area()

    if archivo.exists():
        data = ObtenerArchivo(str(archivo), EnConfig=False)
        rprint(f"[yellow]⚠[/]  Ya hay un área configurada: [dim]{data.get('url')}[/]")
        rprint(f"  Usa [cyan]proyectool area remove[/] primero para reemplazarla.")
        raise typer.Exit()

    EscribirArchivo(str(archivo), {"url": url})
    rprint(f"[green]✓[/] Área guardada en [dim]{archivo}[/]")


@app.command("remove")
def remove_area() -> None:
    """🗑️   Elimina el área de este folder."""
    archivo = _ruta_area()

    if not archivo.exists():
        rprint("[red]✗[/] No hay área configurada en este folder.")
        raise typer.Exit(1)

    archivo.unlink()
    rprint("[green]✓[/] Área eliminada")
