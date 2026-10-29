from proyectool.commands.proyecto import _nombre_con_numero


def test_nombre_con_numero():
    assert _nombre_con_numero("Mi video", []) == "1.Mi_video"
    assert _nombre_con_numero(" Mi  video ", ["1.A", "2_B", "otro"]) == "3.Mi_video"
    assert _nombre_con_numero("x", ["09.A", "3.B"]) == "10.x"
    assert _nombre_con_numero("x", ["01.A"]) == "02.x"
    assert _nombre_con_numero("5.Ya numerado", ["9.A"]) == "5.Ya_numerado"


if __name__ == "__main__":
    test_nombre_con_numero()
    print("ok")
