"""Crea (o cambia) la contraseña de acceso del taxímetro.

Uso, desde la raíz del proyecto:
    python -m scripts.set_password

La contraseña se pide por teclado sin mostrarla y nunca se guarda en claro.
Solo se escribe config/security.json (sal + hash), que está fuera de git.
"""
import getpass
import json
import os
import sys

from src.infrastructure.auth import RUTA_SECURITY, crear_registro_password

LONGITUD_MINIMA = 8


def main():
    password = getpass.getpass("Nueva contraseña: ")
    if len(password) < LONGITUD_MINIMA:
        sys.exit(f"La contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.")
    if password != getpass.getpass("Repite la contraseña: "):
        sys.exit("Las contraseñas no coinciden.")

    registro = crear_registro_password(password)

    # Permisos 600: solo el propietario puede leer el fichero.
    descriptor = os.open(RUTA_SECURITY, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2)

    print(f"Contraseña guardada en {RUTA_SECURITY}")


if __name__ == "__main__":
    main()
