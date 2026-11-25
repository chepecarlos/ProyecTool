from datetime import datetime

from proyectool.commands.pedido import _cumple, _en_proceso, _parsear_filtros, _repetidas
from proyectool.notion_api import valor_propiedad


def test_valor_propiedad():
    assert valor_propiedad({"type": "rich_text", "rich_text": [{"plain_text": "2228"}, {"plain_text": "8350"}]}) == "22288350"
    assert valor_propiedad({"type": "number", "number": 22288350}) == "22288350"
    assert valor_propiedad({"type": "checkbox", "checkbox": False}) == "false"
    assert valor_propiedad({"type": "status", "status": {"name": "En camino"}}) == "En camino"
    assert valor_propiedad({"type": "formula", "formula": {"type": "string", "string": "x"}}) == "x"
    assert valor_propiedad({"type": "select", "select": None}) == ""
    assert valor_propiedad(None) == ""


def test_filtros():
    f = _parsear_filtros(["Terminado=false", "Estado = en camino"])
    assert f == {"Terminado": "false", "Estado": "en camino"}
    props = {"Terminado": {"type": "checkbox", "checkbox": False},
             "Estado": {"type": "select", "select": {"name": "En Camino"}}}
    assert _cumple(props, f)
    assert not _cumple(props, {"Terminado": "true"})
    assert _cumple(props, {})


def test_en_proceso():
    ev = lambda f, h, e: {"fecha": f, "hora": h, "estado": e}
    ahora = datetime(2026, 11, 26, 20, 0, 0)
    entregada = [ev("24/11/2026", "14:18:01", "ENTREGADA"), ev("23/11/2026", "19:43:41", "EN ALMACEN")]
    assert _en_proceso(entregada, ahora) == "18 h"  # se detiene en la entrega
    camino = [ev("24/11/2026", "08:50:07", "EN TRANSITO"), ev("23/11/2026", "19:43:41", "EN ALMACEN")]
    assert _en_proceso(camino, ahora) == "3 d 0 h"  # sigue contando hasta ahora


def test_repetidas():
    pag = lambda n: {"properties": {"G": {"type": "number", "number": n}}}
    ps = [pag(1), pag(2), pag(1), pag(None)]
    r = _repetidas(ps, "G")
    assert list(r) == ["1"] and len(r["1"]) == 2


if __name__ == "__main__":
    test_repetidas()
    test_en_proceso()
    test_valor_propiedad()
    test_filtros()
    print("ok")
