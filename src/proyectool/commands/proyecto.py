"""Comandos para gestionar Proyectos."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo
from proyectool.notion_api import extraer_id_url, obtener_datos_proyecto, obtener_pagina, obtener_titulo

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

console = Console()

PROYECTO_FILE = Path(".proyectool") / "proyecto.md"
AREA_FILE     = Path(".proyectool") / "area.md"


def _ruta_proyecto() -> Path:
    return Path.cwd() / PROYECTO_FILE


def _ruta_area() -> Path:
    return Path.cwd() / AREA_FILE


@app.command("list")
def list_proyectos() -> None:
    """📋  Muestra el proyecto del folder actual."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint(f"  Usa: [cyan]proyectool proyecto add <url>[/]")
        return

    if data.get("titulo"):
        rprint(f"[cyan]título:[/] {data.get('titulo')}")
    rprint(f"[cyan]url:[/]    {data.get('url', '—')}")
    if data.get("id"):
        rprint(f"[cyan]id:[/]     {data.get('id')}")


@app.command("add")
def add_proyecto(
    url: str = typer.Argument(..., help="URL del proyecto en Notion."),
) -> None:
    """➕  Configura el proyecto de este folder."""
    archivo = _ruta_proyecto()

    # Validar que no exista un área ya configurada
    if _ruta_area().exists():
        data_area = ObtenerArchivo(str(_ruta_area()), EnConfig=False)
        nombre = data_area.get("titulo") or data_area.get("url", "—")
        rprint(f"[red]✗[/]  Este folder ya está configurado como [bold]área[/]: [dim]{nombre}[/]")
        rprint(f"  Un folder no puede ser área y proyecto a la vez.")
        rprint(f"  Usa [cyan]proyectool area remove[/] primero.")
        raise typer.Exit(1)

    if archivo.exists():
        data = ObtenerArchivo(str(archivo), EnConfig=False)
        rprint(f"[yellow]⚠[/]  Ya hay un proyecto configurado: [dim]{data.get('url')}[/]")
        rprint(f"  Usa [cyan]proyectool proyecto remove[/] primero para reemplazarlo.")
        raise typer.Exit()

    # Extraer ID de Notion desde la URL
    page_id = extraer_id_url(url)
    titulo = None

    if page_id:
        with console.status("[dim]Consultando Notion...[/]"):
            page_data = obtener_pagina(page_id)
            if page_data:
                titulo = obtener_titulo(page_data)

    # Armar datos a guardar
    data = {"url": url}
    if page_id:
        data["id"] = page_id
    if titulo:
        data["titulo"] = titulo

    EscribirArchivo(str(archivo), data)

    if titulo:
        rprint(f"[green]✓[/] Proyecto [bold]{titulo}[/] guardado en [dim]{archivo}[/]")
    else:
        rprint(f"[green]✓[/] Proyecto guardado en [dim]{archivo}[/]")
        if not page_id:
            rprint(f"  [yellow]⚠[/] No se pudo extraer el ID de la URL.")
        else:
            rprint(f"  [yellow]⚠[/] No se pudo obtener el título (verifica el token con [cyan]proyectool notion config[/]).")


@app.command("info")
def info_proyecto() -> None:
    """📊  Muestra el estado del proyecto desde Notion."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint(f"  Usa: [cyan]proyectool proyecto add <url>[/]")
        raise typer.Exit()

    page_id = data.get("id")
    if not page_id:
        rprint("[red]✗[/]  El proyecto no tiene ID de Notion guardado.")
        raise typer.Exit(1)

    with console.status("[dim]Consultando Notion...[/]"):
        page_data = obtener_pagina(page_id)

    if not page_data:
        rprint("[red]✗[/]  No se pudo obtener el proyecto desde Notion.")
        rprint(f"  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)

    info = obtener_datos_proyecto(page_data)

    # Colores por estado
    ESTADO_COLOR = {
        "idea": "dim",
        "desarrollo": "blue",
        "guion": "cyan",
        "grabado": "yellow",
        "edicion": "yellow",
        "tomab": "orange3",
        "revision": "magenta",
        "preparado": "green",
        "publicado": "bright_green",
        "analizando": "bright_cyan",
    }

    estado = info["estado"] or "—"
    color_estado = ESTADO_COLOR.get(estado, "white")

    table = Table(title=f"📁  {info['titulo']}", highlight=True, show_header=False)
    table.add_column("Campo",  style="cyan", no_wrap=True)
    table.add_column("Valor")

    table.add_row("Estado",    Text(estado, style=f"bold {color_estado}"))
    table.add_row("Canal",     info["canal"]    or "[dim]—[/]")
    table.add_row("Asignado",  info["asignado"] or "[dim]—[/]")
    table.add_row("Blender",   info["blender"]  or "[dim]—[/]")
    table.add_row("Tareas",    info["cantidad_tareas"] or f"{len(info['tareas_ids'])} tareas")
    table.add_row("Fecha límite", info["hacer_para"] or "[dim]—[/]")
    table.add_row("Terminado", "✅ sí" if info["terminado"] else "⬜ no")
    table.add_row("URL",       f"[dim]{info['url']}[/]")

    rprint(table)


@app.command("remove")
def remove_proyecto() -> None:
    """🗑️   Elimina el proyecto de este folder."""
    archivo = _ruta_proyecto()

    if not archivo.exists():
        rprint("[red]✗[/] No hay proyecto configurado en este folder.")
        raise typer.Exit(1)

    archivo.unlink()
    rprint("[green]✓[/] Proyecto eliminado")
