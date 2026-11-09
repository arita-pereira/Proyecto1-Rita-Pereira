import hashlib
import hmac
import json
import os
import secrets

RUTA_SECURITY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "security.json",
)

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 600_000
TAMANO_SAL = 16


class ConfiguracionSeguridadError(Exception):
    """El fichero de seguridad no existe o no tiene el formato esperado."""


def _derivar_hash(password: str, sal: bytes, iteraciones: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, iteraciones)


def crear_registro_password(password: str, iteraciones: int = ITERACIONES) -> dict:
    """Genera el registro a guardar en security.json: sal aleatoria nueva y hash derivado."""
    sal = secrets.token_bytes(TAMANO_SAL)
    return {
        "algorithm": ALGORITMO,
        "iterations": iteraciones,
        "salt": sal.hex(),
        "password_hash": _derivar_hash(password, sal, iteraciones).hex(),
    }


def cargar_registro(ruta: str = RUTA_SECURITY) -> dict:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            registro = json.load(f)
    except FileNotFoundError:
        raise ConfiguracionSeguridadError(
            "No existe config/security.json. Créalo con: python -m scripts.set_password"
        )

    campos = ("algorithm", "iterations", "salt", "password_hash")
    if any(campo not in registro for campo in campos) or registro["algorithm"] != ALGORITMO:
        raise ConfiguracionSeguridadError(
            "config/security.json tiene un formato antiguo o no válido. "
            "Vuelve a crearlo con: python -m scripts.set_password"
        )
    return registro


def verificar_password(password_introducida: str, ruta: str = RUTA_SECURITY) -> bool:
    registro = cargar_registro(ruta)
    sal = bytes.fromhex(registro["salt"])
    hash_guardado = bytes.fromhex(registro["password_hash"])
    hash_introducido = _derivar_hash(password_introducida, sal, registro["iterations"])
    return hmac.compare_digest(hash_introducido, hash_guardado)
