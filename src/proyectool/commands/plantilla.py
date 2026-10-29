"""Comandos para gestionar la plantilla de proyectos de un Área."""

from pathlib import Path

import typer
from rich import print as rprint

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

AREA_FILE = Path(".proyectool") / "area.md"


def _leer_area() -> dict:
    data = ObtenerArchivo(str(Path.cwd() / AREA_FILE), EnConfig=False)
    if not data:
        rprint("[red]✗[/]  Las plantillas solo se pueden usar en un folder configurado como área.")
        rprint("  Usa: [cyan]proyectool area add <url>[/]")
        raise typer.Exit(1)
    return data


@app.command("definir")
def definir_plantilla(
    ruta: Path = typer.Argument(..., help="Folder o archivo que se copiará al crear un proyecto."),
) -> None:
    """📐  Define la plantilla de proyectos de esta área."""
    data = _leer_area()
    ruta = ruta.expanduser().resolve()

    if not ruta.exists():
        rprint(f"[red]✗[/]  No existe: [dim]{ruta}[/]")
        raise typer.Exit(1)

    data["plantilla"] = str(ruta)
    EscribirArchivo(str(Path.cwd() / AREA_FILE), data)
    tipo = "folder" if ruta.is_dir() else "archivo"
    rprint(f"[green]✓[/] Plantilla ({tipo}) definida: [dim]{ruta}[/]")


@app.command("tareas")
def definir_tareas(
    tareas: list[str] = typer.Argument(..., help='Tareas iniciales, ej: "Guion" "Grabar" "Editar".'),
) -> None:
    """✅  Define las tareas que se crean en Notion con cada proyecto nuevo."""
    data = _leer_area()
    data["tareas"] = tareas
    EscribirArchivo(str(Path.cwd() / AREA_FILE), data)
    rprint(f"[green]✓[/] {len(tareas)} tareas iniciales definidas.")


@app.command("list")
def list_plantilla() -> None:
    """📋  Muestra la plantilla y tareas iniciales de esta área."""
    data = _leer_area()
    if not data.get("plantilla") and not data.get("tareas"):
        rprint("[yellow]⚠[/]  Esta área no tiene plantilla ni tareas (se heredan de áreas superiores si existen).")
        rprint("  Usa: [cyan]proyectool plantilla definir <folder o archivo>[/]")
        return
    rprint(f"[cyan]plantilla:[/] {data.get('plantilla', '—')}")
    for t in data.get("tareas", []):
        rprint(f"  • {t}")
