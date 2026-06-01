"""Comandos para gestionar Proyectos."""

import re
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo
from proyectool.notion_api import (
    archivar_pagina,
    crear_proyecto,
    extraer_id_url,
    obtener_datos_proyecto,
    obtener_db_configurada,
    obtener_db_padre,
    obtener_pagina,
    obtener_titulo,
)

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

console = Console()

PROYECTO_FILE = Path(".proyectool") / "proyecto.md"
AREA_FILE     = Path(".proyectool") / "area.md"


def _ruta_proyecto() -> Path:
    return Path.cwd() / PROYECTO_FILE


def _ruta_area() -> Path:
    return Path.cwd() / AREA_FILE


def _limpiar_nombre_folder(nombre: str) -> str:
    """Convierte el nombre de un folder en un título legible.

    Ejemplos:
        '1.Proyecto_ejemplo'  → 'Proyecto ejemplo'
        '1.ProyectoEjemplo'   → 'Proyecto Ejemplo'
        '01_MiProyecto'       → 'Mi Proyecto'
        'mi-proyecto-demo'    → 'Mi proyecto demo'
    """
    # Quitar prefijo numérico: "1.", "01.", "1_", "01-", etc.
    nombre = re.sub(r'^\d+[._\-\s]+', '', nombre)
    # Separar camelCase: "ProyectoEjemplo" → "Proyecto Ejemplo"
    nombre = re.sub(r'([a-z])([A-Z])', r'\1 \2', nombre)
    # Reemplazar separadores (._-) con espacios
    nombre = re.sub(r'[._\-]+', ' ', nombre)
    # Limpiar espacios múltiples
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    # Capitalizar primera letra
    return nombre[0].upper() + nombre[1:] if nombre else nombre


@app.command("list")
def list_proyectos() -> None:
    """📋  Muestra el proyecto del folder actual."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint("  Usa: [cyan]proyectool proyecto add <url>[/]")
        return

    if data.get("titulo"):
        rprint(f"[cyan]título:[/] {data.get('titulo')}")
    rprint(f"[cyan]url:[/]    {data.get('url', '—')}")
    if data.get("id"):
        rprint(f"[cyan]id:[/]     {data.get('id')}")


@app.command("add")
def add_proyecto(
    url: str = typer.Argument(None, help="URL del proyecto en Notion. Si se omite, se crea uno nuevo."),
) -> None:
    """➕  Vincula o crea el proyecto de este folder en Notion.

    Sin URL: busca un área en el folder padre y crea el proyecto automáticamente.
    Con URL: vincula el folder a un proyecto existente en Notion.
    """
    archivo = _ruta_proyecto()

    # Validar que no exista un área ya configurada en este folder
    if _ruta_area().exists():
        data_area = ObtenerArchivo(str(_ruta_area()), EnConfig=False)
        nombre = data_area.get("titulo") or data_area.get("url", "—")
        rprint(f"[red]✗[/]  Este folder ya está configurado como [bold]área[/]: [dim]{nombre}[/]")
        rprint("  Un folder no puede ser área y proyecto a la vez.")
        rprint("  Usa [cyan]proyectool area remove[/] primero.")
        raise typer.Exit(1)

    if archivo.exists():
        data = ObtenerArchivo(str(archivo), EnConfig=False)
        rprint(f"[yellow]⚠[/]  Ya hay un proyecto configurado: [dim]{data.get('url')}[/]")
        rprint("  Usa [cyan]proyectool proyecto remove[/] primero para reemplazarlo.")
        raise typer.Exit()

    # ── Modo creación: sin URL ────────────────────────────────────────────────
    if url is None:
        nombre_folder = _limpiar_nombre_folder(Path.cwd().name)

        # Buscar área hasta 3 niveles arriba (padre, abuelo, bisabuelo)
        ruta_area_padre = None
        directorio = Path.cwd()
        for _ in range(3):
            directorio = directorio.parent
            candidato = directorio / ".proyectool" / "area.md"
            if candidato.exists():
                ruta_area_padre = candidato
                break

        if ruta_area_padre is None:
            rprint("[red]✗[/]  No se pasó URL y no se encontró un área en los 3 niveles superiores.")
            rprint("  Opciones:")
            rprint("    • Pasa una URL:   [cyan]proyectool proyecto add <url>[/]")
            rprint("    • Configura área en un folder ancestro y luego vuelve a intentarlo.")
            raise typer.Exit(1)

        data_area = ObtenerArchivo(str(ruta_area_padre), EnConfig=False)
        area_id   = data_area.get("id")
        area_nombre = data_area.get("titulo") or area_id

        if not area_id:
            rprint("[red]✗[/]  El área del folder padre no tiene ID de Notion.")
            raise typer.Exit(1)

        db_proyectos = obtener_db_configurada("db_proyectos")
        if not db_proyectos:
            rprint("[red]✗[/]  No hay base de datos de proyectos configurada.")
            rprint("  Configúrala con: [cyan]proyectool notion config --db-proyectos <id>[/]")
            raise typer.Exit(1)

        rprint(f"[dim]Creando proyecto [bold]{nombre_folder}[/] en Notion bajo el área [bold]{area_nombre}[/]...[/]")

        with console.status("[dim]Creando en Notion...[/]"):
            page_data = crear_proyecto(nombre_folder, area_id=area_id)

        if not page_data:
            rprint("[red]✗[/]  No se pudo crear el proyecto en Notion.")
            rprint("  Verifica el token con [cyan]proyectool notion config[/]")
            raise typer.Exit(1)

        page_id = page_data.get("id")
        titulo  = obtener_titulo(page_data) or nombre_folder
        url_notion = page_data.get("url", "")

        EscribirArchivo(str(archivo), {"url": url_notion, "id": page_id, "titulo": titulo})
        rprint(f"[green]✓[/] Proyecto [bold]{titulo}[/] creado en Notion.")
        rprint(f"  Área: [cyan]{area_nombre}[/]")
        rprint(f"  URL:  [dim]{url_notion}[/]")
        return

    # ── Modo vinculación: con URL ─────────────────────────────────────────────
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

    # Validar que la página pertenezca a la base de datos de proyectos
    db_proyectos = obtener_db_configurada("db_proyectos")
    if db_proyectos:
        db_padre = obtener_db_padre(page_data)
        if db_padre and db_padre != db_proyectos:
            titulo_erronea = obtener_titulo(page_data) or page_id
            rprint(f"[red]✗[/]  La página [bold]{titulo_erronea}[/] no pertenece a la base de datos de Proyectos.")
            rprint("  Asegúrate de pasar la URL de una página del database de Proyectos.")
            raise typer.Exit(1)

    titulo = obtener_titulo(page_data)

    data = {"url": url, "id": page_id}
    if titulo:
        data["titulo"] = titulo

    EscribirArchivo(str(archivo), data)

    if titulo:
        rprint(f"[green]✓[/] Proyecto [bold]{titulo}[/] guardado en [dim]{archivo}[/]")
    else:
        rprint(f"[green]✓[/] Proyecto guardado en [dim]{archivo}[/]")


@app.command("info")
def info_proyecto() -> None:
    """📊  Muestra el estado del proyecto desde Notion."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint("  Usa: [cyan]proyectool proyecto add <url>[/]")
        raise typer.Exit()

    page_id = data.get("id")
    if not page_id:
        rprint("[red]✗[/]  El proyecto no tiene ID de Notion guardado.")
        raise typer.Exit(1)

    with console.status("[dim]Consultando Notion...[/]"):
        page_data = obtener_pagina(page_id)

    if not page_data:
        rprint("[red]✗[/]  No se pudo obtener el proyecto desde Notion.")
        rprint("  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)

    info = obtener_datos_proyecto(page_data)

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
    table.add_column("Campo", style="cyan", no_wrap=True)
    table.add_column("Valor")

    table.add_row("Estado",       Text(estado, style=f"bold {color_estado}"))
    table.add_row("Canal",        info["canal"]    or "[dim]—[/]")
    table.add_row("Asignado",     info["asignado"] or "[dim]—[/]")
    table.add_row("Blender",      info["blender"]  or "[dim]—[/]")
    table.add_row("Tareas",       info["cantidad_tareas"] or f"{len(info['tareas_ids'])} tareas")
    table.add_row("Fecha límite", info["hacer_para"] or "[dim]—[/]")
    table.add_row("Terminado",    "✅ sí" if info["terminado"] else "⬜ no")
    table.add_row("URL",          f"[dim]{info['url']}[/]")

    rprint(table)


@app.command("archivar")
def archivar_proyecto(
    deshacer: bool = typer.Option(False, "--deshacer", "-d", help="Desarchiva el proyecto en lugar de archivarlo."),
) -> None:
    """📦  Archiva (o desarchiva) el proyecto en Notion."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint("  Usa: [cyan]proyectool proyecto add <url>[/]")
        raise typer.Exit()

    page_id = data.get("id")
    if not page_id:
        rprint("[red]✗[/]  El proyecto no tiene ID de Notion guardado.")
        raise typer.Exit(1)

    accion = "Desarchivando" if deshacer else "Archivando"
    titulo = data.get("titulo") or page_id

    with console.status(f"[dim]{accion} en Notion...[/]"):
        ok = archivar_pagina(page_id, archivar=not deshacer)

    if ok:
        icono = "📤" if deshacer else "📦"
        verbo = "desarchivado" if deshacer else "archivado"
        rprint(f"[green]✓[/] {icono} Proyecto [bold]{titulo}[/] {verbo} en Notion.")
    else:
        rprint("[red]✗[/]  No se pudo actualizar el proyecto en Notion.")
        rprint("  Verifica el token con [cyan]proyectool notion config[/]")
        raise typer.Exit(1)


@app.command("remove")
def remove_proyecto() -> None:
    """🗑️   Elimina el proyecto de este folder."""
    archivo = _ruta_proyecto()

    if not archivo.exists():
        rprint("[red]✗[/] No hay proyecto configurado en este folder.")
        raise typer.Exit(1)

    archivo.unlink()
    rprint("[green]✓[/] Proyecto eliminado")
