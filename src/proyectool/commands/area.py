"""Comandos para gestionar Áreas."""

from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo
from proyectool.notion_api import (
    archivar_pagina,
    extraer_id_url,
    obtener_datos_area,
    obtener_db_configurada,
    obtener_db_padre,
    obtener_pagina,
    obtener_titulo,
)

console = Console()

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

AREA_FILE     = Path(".proyectool") / "area.md"
PROYECTO_FILE = Path(".proyectool") / "proyecto.md"


def _ruta_area() -> Path:
    return Path.cwd() / AREA_FILE


def _ruta_proyecto() -> Path:
    return Path.cwd() / PROYECTO_FILE


@app.command("list")
def list_areas() -> None:
    """📋  Muestra el área del folder actual."""
    archivo = _ruta_area()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay área configurada en este folder.")
        rprint("  Usa: [cyan]proyectool area add <url>[/]")
        return

    if data.get("titulo"):
        rprint(f"[cyan]título:[/] {data.get('titulo')}")
    rprint(f"[cyan]url:[/]    {data.get('url', '—')}")
    if data.get("id"):
        rprint(f"[cyan]id:[/]     {data.get('id')}")


@app.command("info")
def info_area() -> None:
    """📊  Muestra la información del área desde Notion."""
    archivo = _ruta_area()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay área configurada en este folder.")
        rprint("  Usa: [cyan]proyectool area add <url>[/]")
        raise typer.Exit()

    page_id = data.get("id")
    if not page_id:
        rprint("[red]✗[/]  El área no tiene ID de Notion guardado.")
        raise typer.Exit(1)

    with console.status("[dim]Consultando Notion...[/]"):
        page_data = obtener_pagina(page_id)

    if not page_data:
        rprint("[red]✗[/]  No se pudo obtener el área desde Notion.")
        rprint("  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)

    info = obtener_datos_area(page_data)

    TIPO_COLOR = {"Area": "blue", "Recurso": "magenta"}
    tipo = info["tipo"] or "—"
    color_tipo = TIPO_COLOR.get(tipo, "white")

    table = Table(title=f"🗂️   {info['titulo']}", highlight=True, show_header=False)
    table.add_column("Campo", style="cyan", no_wrap=True)
    table.add_column("Valor")

    table.add_row("Tipo",      Text(tipo, style=f"bold {color_tipo}"))
    table.add_row("Proyectos", str(len(info["proyectos_ids"])) if info["proyectos_ids"] else "[dim]0[/]")
    table.add_row("Notas",     str(len(info["notas_ids"]))     if info["notas_ids"]     else "[dim]0[/]")
    table.add_row("Recursos",  str(len(info["recursos_ids"]))  if info["recursos_ids"]  else "[dim]0[/]")
    table.add_row("Archivado", "✅ sí" if info["archivo"] else "⬜ no")
    table.add_row("URL",       f"[dim]{info['url']}[/]")

    rprint(table)


@app.command("add")
def add_area(
    url: str = typer.Argument(..., help="URL del área en Notion."),
) -> None:
    """➕  Configura el área de este folder."""
    archivo = _ruta_area()

    # Validar que no exista un proyecto ya configurado
    if _ruta_proyecto().exists():
        data_proyecto = ObtenerArchivo(str(_ruta_proyecto()), EnConfig=False)
        nombre = data_proyecto.get("titulo") or data_proyecto.get("url", "—")
        rprint(f"[red]✗[/]  Este folder ya está configurado como [bold]proyecto[/]: [dim]{nombre}[/]")
        rprint("  Un folder no puede ser proyecto y área a la vez.")
        rprint("  Usa [cyan]proyectool proyecto remove[/] primero.")
        raise typer.Exit(1)

    if archivo.exists():
        data = ObtenerArchivo(str(archivo), EnConfig=False)
        rprint(f"[yellow]⚠[/]  Ya hay un área configurada: [dim]{data.get('url')}[/]")
        rprint("  Usa [cyan]proyectool area remove[/] primero para reemplazarla.")
        raise typer.Exit()

    # Extraer ID de Notion desde la URL
    page_id = extraer_id_url(url)
    if not page_id:
        rprint("[red]✗[/]  No se pudo extraer el ID de la URL.")
        rprint("  Asegúrate de usar una URL de Notion válida.")
        raise typer.Exit(1)

    with console.status("[dim]Consultando Notion...[/]"):
        page_data = obtener_pagina(page_id)

    if not page_data:
        rprint("[red]✗[/]  No se pudo obtener la página desde Notion.")
        rprint("  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)

    # Validar que la página pertenezca a la base de datos de áreas
    db_area = obtener_db_configurada("db_area")
    if db_area:
        db_padre = obtener_db_padre(page_data)
        if db_padre and db_padre != db_area:
            titulo_erronea = obtener_titulo(page_data) or page_id
            rprint(f"[red]✗[/]  La página [bold]{titulo_erronea}[/] no pertenece a la base de datos de Áreas.")
            rprint("  Asegúrate de pasar la URL de una página del database de Áreas/Recursos.")
            raise typer.Exit(1)

    titulo = obtener_titulo(page_data)

    data = {"url": url, "id": page_id}
    if titulo:
        data["titulo"] = titulo

    EscribirArchivo(str(archivo), data)

    if titulo:
        rprint(f"[green]✓[/] Área [bold]{titulo}[/] guardada en [dim]{archivo}[/]")
    else:
        rprint(f"[green]✓[/] Área guardada en [dim]{archivo}[/]")


@app.command("archivar")
def archivar_area(
    deshacer: bool = typer.Option(False, "--deshacer", "-d", help="Desarchiva el área en lugar de archivarla."),
) -> None:
    """📦  Archiva (o desarchiva) el área en Notion."""
    archivo = _ruta_area()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay área configurada en este folder.")
        rprint("  Usa: [cyan]proyectool area add <url>[/]")
        raise typer.Exit()

    page_id = data.get("id")
    if not page_id:
        rprint("[red]✗[/]  El área no tiene ID de Notion guardado.")
        raise typer.Exit(1)

    accion = "Desarchivando" if deshacer else "Archivando"
    titulo = data.get("titulo") or page_id

    with console.status(f"[dim]{accion} en Notion...[/]"):
        ok = archivar_pagina(page_id, archivar=not deshacer)

    if ok:
        icono = "📤" if deshacer else "📦"
        verbo = "desarchivada" if deshacer else "archivada"
        rprint(f"[green]✓[/] {icono} Área [bold]{titulo}[/] {verbo} en Notion.")
    else:
        rprint("[red]✗[/]  No se pudo actualizar el área en Notion.")
        rprint("  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)


@app.command("remove")
def remove_area() -> None:
    """🗑️   Elimina el área de este folder."""
    archivo = _ruta_area()

    if not archivo.exists():
        rprint("[red]✗[/] No hay área configurada en este folder.")
        raise typer.Exit(1)

    archivo.unlink()
    rprint("[green]✓[/] Área eliminada")
