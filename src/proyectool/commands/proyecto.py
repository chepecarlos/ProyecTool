"""Comandos para gestionar Proyectos."""

import os
import re
import shutil
import webbrowser
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
    crear_tarea,
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
AREA_FILE = Path(".proyectool") / "area.md"


def _ruta_proyecto() -> Path:
    return Path.cwd() / PROYECTO_FILE


def _ruta_area() -> Path:
    return Path.cwd() / AREA_FILE


def _limpiar_nombre_folder(nombre: str) -> str:
    """Convierte el nombre de un folder en un título legible.

    Ejemplos:
        '1.Proyecto_ejemplo'  → '1 Proyecto ejemplo'
        '1.ProyectoEjemplo'   → '1 Proyecto ejemplo'
        '01_MiProyecto'       → '01 Mi proyecto'
        'mi-proyecto-demo'    → 'Mi proyecto demo'
    """
    # Extraer prefijo numérico si existe: "1.", "01.", "1_", "01-", etc.
    match = re.match(r'^(\d+)[._\-\s]+', nombre)
    prefijo = match.group(1) + ' ' if match else ''
    if match:
        nombre = nombre[match.end():]
    # Separar camelCase: "ProyectoEjemplo" → "Proyecto Ejemplo"
    nombre = re.sub(r'([a-z])([A-Z])', r'\1 \2', nombre)
    # Reemplazar separadores (._-) con espacios
    nombre = re.sub(r'[._\-]+', ' ', nombre)
    # Limpiar espacios múltiples y pasar a minúsculas
    nombre = re.sub(r'\s+', ' ', nombre).strip().lower()
    # Capitalizar solo la primera letra del nombre
    nombre = nombre[0].upper() + nombre[1:] if nombre else nombre
    return (prefijo + nombre).strip()


def _areas_ancestras(folder: Path) -> list[dict]:
    """Datos de las áreas en los 3 niveles superiores de `folder`, de la más cercana a la más lejana."""
    areas = []
    for directorio in list(folder.parents)[:3]:
        data = ObtenerArchivo(str(directorio / AREA_FILE), EnConfig=False)
        if data:
            areas.append(data)
    return areas


def _nombre_con_numero(nombre: str, existentes: list[str]) -> str:
    """'Mi video' → '3.Mi_video' si el número más alto entre `existentes` es 2.

    Si el nombre ya trae número ('5.Mi video') se respeta.
    """
    nombre = re.sub(r"\s+", "_", nombre.strip())
    if re.match(r"^\d+[._\-]", nombre):
        return nombre
    numeros = [m.group(1) for e in existentes if (m := re.match(r"^(\d+)[._\-\s]", e))]
    if not numeros:
        return f"1.{nombre}"
    mayor = max(numeros, key=int)
    # Respeta ceros a la izquierda: '09' → '10', '01' → '02'
    return f"{str(int(mayor) + 1).zfill(len(mayor))}.{nombre}"


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
        areas = _areas_ancestras(Path.cwd())

        if not areas:
            rprint("[red]✗[/]  No se pasó URL y no se encontró un área en los 3 niveles superiores.")
            rprint("  Opciones:")
            rprint("    • Pasa una URL:   [cyan]proyectool proyecto add <url>[/]")
            rprint("    • Configura área en un folder ancestro y luego vuelve a intentarlo.")
            raise typer.Exit(1)

        data_area = areas[0]
        area_id = data_area.get("id")
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
        titulo = obtener_titulo(page_data) or nombre_folder
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


@app.command("crear")
def crear_proyecto_folder(
    nombre: str = typer.Argument(..., help="Nombre del proyecto (los espacios se cambian por _, el número se pone solo)."),
    sin_notion: bool = typer.Option(False, "--sin-notion", help="Solo crea el folder local, sin Notion ni tareas."),
) -> None:
    """🆕  Crea un folder de proyecto desde la plantilla del área y lo crea en Notion."""
    existentes = [d.name for d in Path.cwd().iterdir() if d.is_dir()]
    destino = Path.cwd() / _nombre_con_numero(nombre, existentes)
    if destino.exists():
        rprint(f"[red]✗[/]  Ya existe: [dim]{destino}[/]")
        raise typer.Exit(1)

    areas = _areas_ancestras(destino)
    if not areas and not sin_notion:
        rprint("[red]✗[/]  No se encontró un área en los 3 niveles superiores.")
        rprint("  Configura una con [cyan]proyectool area add <url>[/] o usa [cyan]--sin-notion[/]")
        raise typer.Exit(1)

    # Plantilla y tareas se heredan del área más cercana que las tenga
    plantilla = next((a["plantilla"] for a in areas if a.get("plantilla")), None)
    tareas = next((a["tareas"] for a in areas if a.get("tareas")), [])

    if plantilla and Path(plantilla).is_dir():
        shutil.copytree(plantilla, destino, ignore=shutil.ignore_patterns(".proyectool"))
    else:
        destino.mkdir()
        if plantilla and Path(plantilla).is_file():
            shutil.copy2(plantilla, destino)
        elif plantilla:
            rprint(f"[yellow]⚠[/]  La plantilla ya no existe: [dim]{plantilla}[/] (se crea folder vacío)")

    rprint(f"[green]✓[/] Folder [bold]{destino.name}[/] creado.")
    if sin_notion:
        return

    # ponytail: reutiliza el modo creación de `add`, que encuentra el área en el folder padre
    os.chdir(destino)
    add_proyecto(url=None)

    if not tareas:
        return
    proyecto_id = ObtenerArchivo(str(_ruta_proyecto()), EnConfig=False).get("id")
    with console.status("[dim]Creando tareas en Notion...[/]"):
        creadas = [t for t in tareas if crear_tarea(t, proyecto_id)]
    for t in creadas:
        rprint(f"  [green]✓[/] Tarea [bold]{t}[/]")
    if len(creadas) < len(tareas):
        rprint(f"[red]✗[/]  No se pudieron crear {len(tareas) - len(creadas)} tareas.")
        rprint("  Revisa [cyan]proyectool notion config --db-tareas <id>[/]")


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

    table.add_row("Estado", Text(estado, style=f"bold {color_estado}"))
    table.add_row("Canal", info["canal"] or "[dim]—[/]")
    table.add_row("Asignado", info["asignado"] or "[dim]—[/]")
    table.add_row("Blender", info["blender"] or "[dim]—[/]")
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


@app.command("open")
def open_proyecto() -> None:
    """🌐  Abre el proyecto en el navegador."""
    archivo = _ruta_proyecto()
    data = ObtenerArchivo(str(archivo), EnConfig=False)

    if not data:
        rprint("[yellow]⚠[/]  No hay proyecto configurado en este folder.")
        rprint("  Usa: [cyan]proyectool proyecto add <url>[/]")
        raise typer.Exit()

    url = data.get("url")
    if not url:
        rprint("[red]✗[/]  El proyecto no tiene URL guardada.")
        raise typer.Exit(1)

    titulo = data.get("titulo") or url
    webbrowser.open(url)
    rprint(f"[green]✓[/] Abriendo [bold]{titulo}[/] en el navegador.")


@app.command("remove")
def remove_proyecto() -> None:
    """🗑️   Elimina el proyecto de este folder."""
    archivo = _ruta_proyecto()

    if not archivo.exists():
        rprint("[red]✗[/] No hay proyecto configurado en este folder.")
        raise typer.Exit(1)

    archivo.unlink()
    rprint("[green]✓[/] Proyecto eliminado")
