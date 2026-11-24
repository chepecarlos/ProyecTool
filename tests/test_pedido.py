from proyectool.commands.pedido import _cumple, _parsear_filtros
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


if __name__ == "__main__":
    test_valor_propiedad()
    test_filtros()
    print("ok")
