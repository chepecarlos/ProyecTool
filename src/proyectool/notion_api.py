"""Funciones para interactuar con la API de Notion."""

import re
import requests
from pathlib import Path

from proyectool.miLibrerias.FuncionesArchivos import ObtenerArchivo
from proyectool.miLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)

# Ruta de configuración (igual que en commands/notion.py)
CONFIG_FILE = Path.home() / ".config" / "proyectool" / "notion.md"

# Versión de la API de Notion
NOTION_VERSION = "2022-06-28"


def _normalizar_id(id_str: str) -> str:
    """Quita guiones de un UUID para comparaciones."""
    return id_str.replace("-", "").lower() if id_str else ""


def _obtener_config() -> dict:
    """Lee la configuración completa de Notion."""
    return ObtenerArchivo(str(CONFIG_FILE), EnConfig=False) or {}


def _obtener_token() -> str | None:
    """Obtiene el token de Notion desde la configuración."""
    return _obtener_config().get("token")


def obtener_db_configurada(campo: str) -> str | None:
    """Devuelve el ID de una base de datos configurada (db_area, db_proyectos).

    Args:
        campo: nombre del campo en la config, ej. 'db_area' o 'db_proyectos'

    Returns:
        ID normalizado (sin guiones) o None si no está configurado.
    """
    valor = _obtener_config().get(campo)
    return _normalizar_id(valor) if valor else None


def obtener_db_padre(page_data: dict) -> str | None:
    """Extrae el database_id del parent de una página (normalizado, sin guiones)."""
    parent = page_data.get("parent", {})
    if parent.get("type") == "database_id":
        return _normalizar_id(parent.get("database_id", ""))
    return None


def extraer_id_url(url: str) -> str | None:
    """Extrae el ID de una página de Notion desde su URL.

    Soporta formatos como:
    - https://www.notion.so/Titulo-de-Pagina-abc123def456789012345678901234ab
    - https://www.notion.so/workspace/abc123def456789012345678901234ab
    - URLs con o sin guiones en el ID

    Returns:
        str | None: ID formateado como UUID (con guiones) o None si no se encontró.
    """
    # Busca UUIDs con o sin guiones al final del path
    patron_uuid = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
    patron_hex  = r'([a-f0-9]{32})'

    url_lower = url.lower().split("?")[0]  # Quitar query params

    # Primero intenta UUID con guiones
    coincidencias = re.findall(patron_uuid, url_lower)
    if coincidencias:
        return coincidencias[-1]

    # Luego intenta 32 hex consecutivos (UUID sin guiones)
    coincidencias = re.findall(patron_hex, url_lower)
    if coincidencias:
        raw = coincidencias[-1]
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"

    return None


def obtener_pagina(page_id: str) -> dict | None:
    """Consulta la API de Notion y devuelve los datos de una página.

    Args:
        page_id: ID de la página en formato UUID.

    Returns:
        dict con la respuesta de Notion, o None si falló.
    """
    token = _obtener_token()
    if not token:
        logger.warning("No hay token de Notion configurado")
        return None

    url_consulta = f"https://api.notion.com/v1/pages/{page_id}"
    cabeceras = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    try:
        respuesta = requests.get(url_consulta, headers=cabeceras, timeout=10)
    except requests.exceptions.Timeout:
        logger.warning("La consulta a Notion tardó demasiado")
        return None
    except Exception as e:
        logger.warning(f"Error al consultar Notion: {e}")
        return None

    if respuesta.status_code == 200:
        return respuesta.json()

    logger.warning(f"Notion respondió con código {respuesta.status_code}")
    return None


def obtener_datos_proyecto(page_data: dict) -> dict:
    """Extrae las propiedades relevantes de una página de Proyecto.

    Returns:
        dict con: titulo, estado, canal, asignado, terminado, hacer_para,
                  cantidad_tareas, tareas_ids, area_ids, blender, url
    """
    props = page_data.get("properties", {})

    def select(key):
        s = props.get(key, {}).get("select")
        return s.get("name") if s else None

    def checkbox(key):
        return props.get(key, {}).get("checkbox", False)

    def fecha(key):
        d = props.get(key, {}).get("date")
        return d.get("start") if d else None

    def relacion(key):
        return [r["id"] for r in props.get(key, {}).get("relation", [])]

    titulo = obtener_titulo(page_data)
    cantidad_tareas = props.get("Cantidad Tareas", {}).get("formula", {}).get("string")

    return {
        "titulo":         titulo,
        "estado":         select("Estado"),
        "canal":          select("Canal"),
        "asignado":       select("Asignado"),
        "blender":        select("Blender"),
        "terminado":      checkbox("Terminado"),
        "archivo":        checkbox("Archivo"),
        "hacer_para":     fecha("Hacer para"),
        "cantidad_tareas": cantidad_tareas,
        "tareas_ids":     relacion("Tarea"),
        "area_ids":       relacion("Área"),
        "url":            page_data.get("url"),
    }


def actualizar_propiedades(page_id: str, propiedades: dict) -> bool:
    """Actualiza propiedades de una página en Notion via PATCH.

    Args:
        page_id: ID de la página a actualizar.
        propiedades: dict con las propiedades en formato de la API de Notion.

    Returns:
        True si se actualizó correctamente, False en caso de error.
    """
    token = _obtener_token()
    if not token:
        logger.warning("No hay token de Notion configurado")
        return False

    url_consulta = f"https://api.notion.com/v1/pages/{page_id}"
    cabeceras = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    try:
        respuesta = requests.patch(
            url_consulta,
            headers=cabeceras,
            json={"properties": propiedades},
            timeout=10,
        )
    except requests.exceptions.Timeout:
        logger.warning("La consulta a Notion tardó demasiado")
        return False
    except Exception as e:
        logger.warning(f"Error al actualizar Notion: {e}")
        return False

    if respuesta.status_code == 200:
        return True

    logger.warning(f"Notion respondió con código {respuesta.status_code}")
    return False


def archivar_pagina(page_id: str, archivar: bool = True) -> bool:
    """Activa o desactiva el checkbox Archivo de una página.

    Args:
        page_id: ID de la página.
        archivar: True para archivar, False para desarchivar.

    Returns:
        True si se actualizó correctamente.
    """
    return actualizar_propiedades(page_id, {"Archivo": {"checkbox": archivar}})


def obtener_datos_area(page_data: dict) -> dict:
    """Extrae las propiedades relevantes de una página de Área/Recurso.

    Returns:
        dict con: titulo, tipo, proyectos_ids, notas_ids, recursos_ids,
                  area_base_ids, archivo, url
    """
    props = page_data.get("properties", {})

    def relacion(key):
        return [r["id"] for r in props.get(key, {}).get("relation", [])]

    def checkbox(key):
        return props.get(key, {}).get("checkbox", False)

    def status(key):
        s = props.get(key, {}).get("status")
        return s.get("name") if s else None

    titulo = obtener_titulo(page_data)

    return {
        "titulo":        titulo,
        "tipo":          status("Tipo"),
        "proyectos_ids": relacion("Proyectos"),
        "notas_ids":     relacion("Notas"),
        "recursos_ids":  relacion("Recursos"),
        "area_base_ids": relacion("Área Base"),
        "archivo":       checkbox("Archivo"),
        "url":           page_data.get("url"),
    }


def obtener_titulo(page_data: dict) -> str | None:
    """Extrae el título plano de los datos de una página de Notion.

    Args:
        page_data: Respuesta JSON de la API de Notion para una página.

    Returns:
        Título como string, o None si no se pudo extraer.
    """
    try:
        propiedades = page_data.get("properties", {})
        for _key, valor in propiedades.items():
            if valor.get("type") == "title":
                fragmentos = valor.get("title", [])
                if fragmentos:
                    return "".join(f.get("plain_text", "") for f in fragmentos)
    except Exception as e:
        logger.warning(f"Error extrayendo título: {e}")
    return None
