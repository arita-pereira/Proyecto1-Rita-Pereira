import logging

import pytest

from src.application.servicio_carrera import (
    CarreraYaActivaError,
    ServicioCarrera,
    SinCarreraActivaError,
)
from src.domain.tarifa import Tarifa


@pytest.fixture
def servicio(bd_temporal):
    return ServicioCarrera(Tarifa(0.02, 0.05), logging.getLogger("taximetro-tests"))


def test_iniciar_deja_la_carrera_parada(servicio, reloj):
    assert servicio.iniciar() == "parado"
    assert servicio.estado_actual()["activa"] is True


def test_no_se_puede_iniciar_dos_veces(servicio, reloj):
    servicio.iniciar()
    with pytest.raises(CarreraYaActivaError):
        servicio.iniciar()


@pytest.mark.parametrize("operacion", ["alternar_estado", "finalizar"])
def test_operaciones_sin_carrera_activa(servicio, operacion):
    with pytest.raises(SinCarreraActivaError):
        getattr(servicio, operacion)()


def test_finalizar_devuelve_total_guarda_y_libera_la_carrera(servicio, reloj):
    servicio.iniciar()
    reloj.avanzar(10)
    servicio.alternar_estado()
    reloj.avanzar(10)

    assert servicio.finalizar() == pytest.approx(0.7)
    assert servicio.estado_actual() == {"activa": False}
    assert len(servicio.historial_del_dia()) == 1


def test_cada_servicio_tiene_su_propia_carrera(bd_temporal, reloj):
    a = ServicioCarrera(Tarifa(0.02, 0.05))
    b = ServicioCarrera(Tarifa(0.02, 0.05))
    a.iniciar()
    assert b.estado_actual() == {"activa": False}
