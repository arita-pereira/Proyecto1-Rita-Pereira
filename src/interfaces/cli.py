from src.application.servicio_carrera import (
    CarreraYaActivaError,
    ServicioCarrera,
    SinCarreraActivaError,
)
from src.infrastructure.auth import verificar_password
from src.infrastructure.logger import configurar_logger
from src.infrastructure.tarifas import cargar_tarifa


def mostrar_menu():
    print("\n--- TAXÍMETRO DIGITAL ---")
    print("1. Iniciar carrera")
    print("2. Cambiar estado (parado/movimiento)")
    print("3. Finalizar carrera y cobrar")
    print("4. Ver histórico del día")
    print("5. Salir")
    print("6. Bloquear aplicación")

def pedir_password(logger):
    while True:
        intento = input("Introduce la contraseña: ")
        if verificar_password(intento):
            print("Acceso concedido.")
            logger.info("Acceso concedido con contraseña correcta.")
            break
        else:
            print("Contraseña incorrecta, inténtalo de nuevo.")
            logger.warning("Intento de acceso con contraseña incorrecta.")

def main():
    logger = configurar_logger()
    servicio = ServicioCarrera(cargar_tarifa(), logger)
    logger.info("Aplicación iniciada por el usuario.")
    pedir_password(logger)

    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ")

        try:
            if opcion == "1":
                estado = servicio.iniciar()
                print(f"Carrera iniciada. Estado: {estado}")

            elif opcion == "2":
                estado = servicio.alternar_estado()
                print(f"Nuevo estado: {estado}")

            elif opcion == "3":
                total = servicio.finalizar()
                print(f"Carrera finalizada. Total a cobrar: {total:.2f} €")

            elif opcion == "4":
                historial = servicio.historial_del_dia()
                if not historial:
                    print("No hay carreras registradas hoy.")
                else:
                    print(f"\n--- HISTÓRICO DE HOY ({len(historial)} carreras) ---")
                    for carrera in historial:
                        print(f"{carrera['hora_inicio']} → {carrera['hora_fin']}: {carrera['total']} €")

            elif opcion == "6":
                print("Aplicación bloqueada.")
                logger.info("Aplicación bloqueada por el usuario.")
                pedir_password(logger)

            elif opcion == "5":
                print("Cerrando aplicación. Hasta luego.")
                logger.info("Aplicación cerrada por el usuario.")
                break

            else:
                print("Opción no válida, intenta de nuevo.")
                logger.warning("Opción no válida seleccionada.")

        except (CarreraYaActivaError, SinCarreraActivaError) as error:
            print(error)

if __name__ == "__main__":
    main()
