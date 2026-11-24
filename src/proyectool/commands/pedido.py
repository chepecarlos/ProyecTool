"""Seguimiento de pedidos: proyectos de un área rastreados en AeroFlash."""

from pathlib import Path

import requests
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo, ObtenerArchivo
from proyectool.notion_api import consultar_db, obtener_db_configurada, obtener_titulo, valor_propiedad

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)

console = Console()

AREA_FILE   = Path(".proyectool") / "area.md"
ESTADO_FILE = Path(".proyectool") / "pedidos.json"

AEROFLASH = "https://info.aeroflash.app"


# ─── AeroFlash ────────────────────────────────────────────────────────────────

def _rastrear(guia: str) -> list[dict]:
    """Eventos de la guía, el más reciente primero (endpoint público, sin login)."""
    r = requests.get(f"{AEROFLASH}/api/v1/tracking/{guia}", timeout=20)
    r.raise_for_status()
    return r.json().get("data") or []


# ─── Filtros ──────────────────────────────────────────────────────────────────

def _parsear_filtros(filtros: list[str]) -> dict:
    """['Terminado=false', 'Estado=En camino'] → {'Terminado': 'false', 'Estado': 'En camino'}"""
    resultado = {}
    for f in filtros:
        if "=" not in f:
            raise typer.BadParameter(f"'{f}' debe tener la forma Campo=valor")
        campo, valor = f.split("=", 1)
        resultado[campo.strip()] = valor.strip()
    return resultado


def _cumple(props: dict, filtros: dict) -> bool:
    """True si todas las propiedades coinciden (sin distinguir mayúsculas)."""
    return all(valor_propiedad(props.get(c)).lower() == v.lower() for c, v in filtros.items())


# ─── Comandos ─────────────────────────────────────────────────────────────────

def _leer_area() -> dict:
    data = ObtenerArchivo(str(Path.cwd() / AREA_FILE), EnConfig=False)
    if not data or not data.get("id"):
        rprint("[yellow]⚠[/]  Este folder no tiene área configurada.")
        rprint("  Usa: [cyan]proyectool area add <url>[/]")
        raise typer.Exit(1)
    return data


@app.command("config")
def config_pedidos(
    campo: str = typer.Option(None, "--campo", "-c", help="Propiedad del proyecto con el número de guía."),
    filtro: list[str] = typer.Option(None, "--filtro", "-f", help="Campo=valor; se puede repetir."),
) -> None:
    """⚙️   Configura qué campo tiene la guía y qué pedidos revisar."""
    data = _leer_area()
    pedidos = data.get("pedidos") or {}

    if campo:
        pedidos["campo"] = campo
    if filtro:
        pedidos["filtros"] = _parsear_filtros(filtro)

    if campo or filtro:
        data["pedidos"] = pedidos
        EscribirArchivo(str(Path.cwd() / AREA_FILE), data)
        rprint("[green]✓[/] Configuración de pedidos guardada.")

    rprint(f"[cyan]campo guía:[/] {pedidos.get('campo', '—')}")
    for c, v in (pedidos.get("filtros") or {}).items():
        rprint(f"[cyan]filtro:[/]     {c} = {v}")


@app.command("estado")
def estado_pedidos() -> None:
    """📦  Consulta en AeroFlash el estado de los pedidos del área."""
    data = _leer_area()
    pedidos = data.get("pedidos") or {}
    campo = pedidos.get("campo")
    if not campo:
        rprint("[yellow]⚠[/]  Falta indicar el campo de la guía.")
        rprint("  Usa: [cyan]proyectool pedido config --campo \"Guía\"[/]")
        raise typer.Exit(1)

    db_proyectos = obtener_db_configurada("db_proyectos")
    if not db_proyectos:
        rprint("[red]✗[/]  Falta db_proyectos. Usa [cyan]proyectool notion config[/]")
        raise typer.Exit(1)

    with console.status("[dim]Consultando Notion...[/]"):
        paginas = consultar_db(db_proyectos, {"property": "Área", "relation": {"contains": data["id"]}})
    if paginas is None:
        rprint("[red]✗[/]  No se pudieron obtener los proyectos del área.")
        raise typer.Exit(1)

    filtros = pedidos.get("filtros") or {}
    lista = [
        (obtener_titulo(p) or "—", valor_propiedad(p["properties"].get(campo)).strip())
        for p in paginas if _cumple(p["properties"], filtros)
    ]
    lista = [(t, g) for t, g in lista if g]
    if not lista:
        rprint(f"[yellow]⚠[/]  Ningún proyecto con [bold]{campo}[/] cumple los filtros.")
        return

    ruta_estado = Path.cwd() / ESTADO_FILE
    previo = ObtenerArchivo(str(ruta_estado), EnConfig=False) or {}

    table = Table(title=f"📦  Pedidos de {data.get('titulo', 'área')}")
    table.add_column("Pedido", style="bold")
    table.add_column("Guía", style="cyan")
    table.add_column("Estado")
    table.add_column("Fecha", style="dim")

    with console.status("[dim]Consultando AeroFlash...[/]"):
        for titulo, guia in lista:
            try:
                eventos = _rastrear(guia)
            except Exception as e:
                table.add_row(titulo, guia, f"[red]error: {e}[/]", "")
                continue
            if not eventos:
                table.add_row(titulo, guia, "[dim]sin información[/]", "")
                continue
            ult = eventos[0]
            fecha = f"{ult['fecha']} {ult['hora']}"
            actual = f"{ult['estado']} ({fecha})"
            cambio = guia in previo and previo[guia] != actual
            table.add_row(titulo, guia, f"[bold yellow]{ult['estado']} ← CAMBIÓ[/]" if cambio else ult["estado"], fecha)
            previo[guia] = actual

    EscribirArchivo(str(ruta_estado), previo)
    rprint(table)
