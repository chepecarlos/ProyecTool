import tempfile
from pathlib import Path

from proyectool.commands.proyecto import PROYECTO_FILE, _folder_con_proyecto, _nombre_con_numero
from proyectool.miLibrerias.FuncionesArchivos import EscribirArchivo


def test_nombre_con_numero():
    assert _nombre_con_numero("Mi video", []) == "1.Mi_video"
    assert _nombre_con_numero(" Mi  video ", ["1.A", "2_B", "otro"]) == "3.Mi_video"
    assert _nombre_con_numero("x", ["09.A", "3.B"]) == "10.x"
    assert _nombre_con_numero("x", ["01.A"]) == "02.x"
    assert _nombre_con_numero("5.Ya numerado", ["9.A"]) == "5.Ya_numerado"


def test_folder_con_proyecto():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "2.Otro").mkdir()
        EscribirArchivo(str(base / "1.Video" / PROYECTO_FILE), {"id": "abc-123"})
        assert _folder_con_proyecto(base, "abc-123").name == "1.Video"
        assert _folder_con_proyecto(base, "zzz") is None


if __name__ == "__main__":
    test_nombre_con_numero()
    test_folder_con_proyecto()
    print("ok")
