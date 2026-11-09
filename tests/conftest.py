import logging
import time

import pytest

import src.infrastructure.historial as historial
import src.interfaces.web as web
from src.application.servicio_carrera import ServicioCarrera
from src.domain.tarifa import Tarifa
from src.infrastructure import auth

PASSWORD_TEST = "clave-de-prueba-1"


class RelojFalso:
    """Sustituye al módulo time dentro de Carrera para controlar los segundos."""

    def __init__(self, inicio):
        self.ahora = inicio

    def time(self):
        return self.ahora

    def avanzar(self, segundos):
        self.ahora += segundos


@pytest.fixture
def reloj(monkeypatch):
    reloj_falso = RelojFalso(time.time())
    monkeypatch.setattr("src.domain.carrera.time", reloj_falso)
    return reloj_falso


@pytest.fixture
def bd_temporal(tmp_path, monkeypatch):
    """Redirige el historial a una base de datos SQLite temporal."""
    monkeypatch.setattr(historial, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(historial, "DB_FILE", str(tmp_path / "historial.db"))
    return tmp_path / "historial.db"


@pytest.fixture
def cliente(tmp_path, monkeypatch, bd_temporal):
    """Cliente de prueba de Flask aislado: BD, contraseña, tarifa y estado propios."""
    ruta_security = tmp_path / "security.json"
    registro = auth.crear_registro_password(PASSWORD_TEST, iteraciones=1000)
    ruta_security.write_text(__import__("json").dumps(registro), encoding="utf-8")

    monkeypatch.setattr(
        web, "verificar_password", lambda p: auth.verificar_password(p, str(ruta_security))
    )
    # Servicio nuevo en cada test: tarifa fija y sin carrera activa heredada.
    monkeypatch.setattr(
        web, "servicio", ServicioCarrera(Tarifa(0.02, 0.05), logging.getLogger("taximetro-tests"))
    )
    monkeypatch.setattr(web, "logger", logging.getLogger("taximetro-tests"))

    web.app.config["TESTING"] = True
    return web.app.test_client()


@pytest.fixture
def cliente_autenticado(cliente):
    with cliente.session_transaction() as sesion:
        sesion["autenticado"] = True
        sesion["nombre"] = "Tester"
    return cliente
