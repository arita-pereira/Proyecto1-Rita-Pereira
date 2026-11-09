import json
import os

from src.domain.tarifa import Tarifa

RUTA_TARIFAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "tarifas.json",
)


def cargar_tarifa(ruta: str = RUTA_TARIFAS) -> Tarifa:
    """Lee las tarifas vigentes de config/tarifas.json."""
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)
    return Tarifa(**datos)
