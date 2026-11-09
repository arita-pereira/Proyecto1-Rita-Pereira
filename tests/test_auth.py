import json

import pytest

from src.infrastructure.auth import (
    ConfiguracionSeguridadError,
    crear_registro_password,
    verificar_password,
)

# Pocas iteraciones solo en tests, para que sean rápidos.
ITERACIONES_TEST = 1000


@pytest.fixture
def ruta_security(tmp_path):
    ruta = tmp_path / "security.json"
    registro = crear_registro_password("clave-de-prueba-1", iteraciones=ITERACIONES_TEST)
    ruta.write_text(json.dumps(registro), encoding="utf-8")
    return str(ruta)


def test_password_correcta(ruta_security):
    assert verificar_password("clave-de-prueba-1", ruta_security) is True


def test_password_incorrecta(ruta_security):
    assert verificar_password("otra-clave", ruta_security) is False


def test_misma_password_genera_sal_y_hash_distintos():
    a = crear_registro_password("clave-de-prueba-1", iteraciones=ITERACIONES_TEST)
    b = crear_registro_password("clave-de-prueba-1", iteraciones=ITERACIONES_TEST)
    assert a["salt"] != b["salt"]
    assert a["password_hash"] != b["password_hash"]


def test_el_registro_no_contiene_la_password_en_claro():
    registro = crear_registro_password("clave-de-prueba-1", iteraciones=ITERACIONES_TEST)
    assert "clave-de-prueba-1" not in json.dumps(registro)


def test_fichero_inexistente(tmp_path):
    with pytest.raises(ConfiguracionSeguridadError):
        verificar_password("lo-que-sea", str(tmp_path / "no-existe.json"))


def test_formato_antiguo_sin_sal(tmp_path):
    ruta = tmp_path / "security.json"
    ruta.write_text(json.dumps({"password_hash": "abc123"}), encoding="utf-8")
    with pytest.raises(ConfiguracionSeguridadError):
        verificar_password("lo-que-sea", str(ruta))
