import sqlite3
from datetime import datetime

import pytest

from src.domain.carrera import Carrera
from src.domain.tarifa import Tarifa
from src.infrastructure.historial import guardar_carrera, obtener_historial_dia

TARIFA = Tarifa(0.02, 0.05)


def carrera_terminada(inicio, segundos_parado=10, segundos_movimiento=10, con_fin=True):
    """Construye una carrera ya finalizada con tiempos y fecha controlados."""
    carrera = Carrera()
    carrera.hora_inicio = inicio.timestamp()
    carrera.segundos_parado = segundos_parado
    carrera.segundos_movimiento = segundos_movimiento
    if con_fin:
        carrera.hora_fin = carrera.hora_inicio + segundos_parado + segundos_movimiento
    return carrera


def test_historial_vacio_si_no_hay_carreras(bd_temporal):
    assert obtener_historial_dia() == []


def test_se_crea_la_base_de_datos_y_la_tabla(bd_temporal):
    obtener_historial_dia()
    assert bd_temporal.exists()
    with sqlite3.connect(bd_temporal) as conexion:
        tablas = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    assert ("carreras",) in tablas


def test_guardar_y_leer_una_carrera(bd_temporal):
    inicio = datetime(2026, 1, 15, 10, 0, 0)
    guardar_carrera(carrera_terminada(inicio), TARIFA)

    registros = obtener_historial_dia("2026-01-15")
    assert registros == [{
        "fecha": "2026-01-15",
        "hora_inicio": "10:00:00",
        "hora_fin": "10:00:20",
        "total": pytest.approx(0.7),
    }]


def test_solo_devuelve_las_carreras_de_la_fecha_pedida(bd_temporal):
    guardar_carrera(carrera_terminada(datetime(2026, 1, 15, 10, 0, 0)), TARIFA)
    guardar_carrera(carrera_terminada(datetime(2026, 1, 16, 9, 0, 0)), TARIFA)

    assert len(obtener_historial_dia("2026-01-15")) == 1
    assert len(obtener_historial_dia("2026-01-16")) == 1
    assert obtener_historial_dia("2026-01-17") == []


def test_por_defecto_devuelve_las_de_hoy(bd_temporal):
    guardar_carrera(carrera_terminada(datetime.now()), TARIFA)
    guardar_carrera(carrera_terminada(datetime(2020, 1, 1, 8, 0, 0)), TARIFA)

    registros = obtener_historial_dia()
    assert len(registros) == 1
    assert registros[0]["fecha"] == datetime.now().strftime("%Y-%m-%d")


def test_varias_carreras_del_mismo_dia(bd_temporal):
    for hora in (8, 9, 10):
        guardar_carrera(carrera_terminada(datetime(2026, 1, 15, hora, 0, 0)), TARIFA)
    assert len(obtener_historial_dia("2026-01-15")) == 3


def test_el_total_se_guarda_redondeado_a_dos_decimales(bd_temporal):
    carrera = carrera_terminada(datetime(2026, 1, 15, 10, 0, 0), 3, 7)  # 0.06 + 0.35 = 0.41
    guardar_carrera(carrera, TARIFA)
    assert obtener_historial_dia("2026-01-15")[0]["total"] == 0.41


def test_carrera_sin_hora_fin_guarda_cadena_vacia(bd_temporal):
    carrera = carrera_terminada(datetime(2026, 1, 15, 10, 0, 0), con_fin=False)
    guardar_carrera(carrera, TARIFA)
    assert obtener_historial_dia("2026-01-15")[0]["hora_fin"] == ""
