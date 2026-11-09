"""Casos de uso del taxímetro.

Orquesta el dominio (Carrera, Tarifa) y la infraestructura (historial, logs)
para que las interfaces (CLI y web) solo se ocupen de leer la entrada del
usuario y mostrar el resultado.
"""
import logging

from src.domain.carrera import Carrera
from src.infrastructure import historial


class CarreraYaActivaError(Exception):
    """Se intentó iniciar una carrera con otra todavía en curso."""


class SinCarreraActivaError(Exception):
    """Se intentó operar sobre una carrera sin haber iniciado ninguna."""


class ServicioCarrera:
    def __init__(self, tarifa, logger=None):
        self.tarifa = tarifa
        self.logger = logger or logging.getLogger("taximetro")
        self.carrera_activa = None

    def iniciar(self) -> str:
        """Inicia una carrera nueva en estado parado y devuelve el estado."""
        if self.carrera_activa is not None:
            self.logger.warning("Intento de iniciar carrera con otra ya en curso.")
            raise CarreraYaActivaError("Ya hay una carrera en curso.")
        self.carrera_activa = Carrera()
        self.logger.info("Carrera iniciada. Estado: parado")
        return self.carrera_activa.estado_actual

    def alternar_estado(self) -> str:
        """Cambia entre parado y movimiento y devuelve el nuevo estado."""
        carrera = self._carrera_requerida()
        nuevo_estado = "movimiento" if carrera.estado_actual == "parado" else "parado"
        carrera.cambiar_estado(nuevo_estado)
        self.logger.info(f"Cambio de estado a: {nuevo_estado}")
        return nuevo_estado

    def finalizar(self) -> float:
        """Cierra la carrera, la guarda en el historial y devuelve el total."""
        carrera = self._carrera_requerida()
        carrera.finalizar_carrera()
        total = round(carrera.calcular_total(self.tarifa), 2)
        historial.guardar_carrera(carrera, self.tarifa)
        self.carrera_activa = None
        self.logger.info(f"Carrera finalizada. Total a cobrar: {total:.2f} €")
        return total

    def estado_actual(self) -> dict:
        """Estado de la carrera en curso con el importe acumulado hasta ahora."""
        if self.carrera_activa is None:
            return {"activa": False}
        return {
            "activa": True,
            "estado": self.carrera_activa.estado_actual,
            "total": round(self.carrera_activa.total_actual(self.tarifa), 2),
        }

    def historial_del_dia(self, fecha: str = None) -> list:
        return historial.obtener_historial_dia(fecha)

    def _carrera_requerida(self):
        if self.carrera_activa is None:
            self.logger.warning("Operación sin carrera activa.")
            raise SinCarreraActivaError("No hay ninguna carrera activa.")
        return self.carrera_activa
