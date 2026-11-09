from flask import Flask, jsonify, request, redirect, url_for, render_template, session
import os
import secrets
from src.application.servicio_carrera import (
    CarreraYaActivaError,
    ServicioCarrera,
    SinCarreraActivaError,
)
from src.infrastructure.auth import verificar_password
from src.infrastructure.logger import configurar_logger
from src.infrastructure.tarifas import cargar_tarifa

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

logger = configurar_logger()

# La clave que firma la cookie de sesión no se guarda en el código: si estuviera en el
# repositorio, cualquiera podría falsificar una sesión autenticada.
clave_secreta = os.environ.get("TAXITECH_SECRET_KEY")
if not clave_secreta:
    clave_secreta = secrets.token_hex(32)
    logger.warning("TAXITECH_SECRET_KEY no definida: se usa una clave aleatoria "
                   "y las sesiones se cerrarán al reiniciar el servidor.")
app.secret_key = clave_secreta

servicio = ServicioCarrera(cargar_tarifa(), logger)
logger.info("Aplicación web iniciada.")


def _no_autenticado():
    return jsonify({"error": "No autenticado"}), 401


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        nombre = request.form.get("nombre")
        if verificar_password(password):
            session["autenticado"] = True
            session["nombre"] = nombre
            logger.info(f"Acceso concedido a {nombre}.")
            return redirect(url_for("home"))
        else:
            logger.warning(f"Intento de acceso con contraseña incorrecta para {nombre}.")
            return render_template("login.html", error="Contraseña incorrecta")
    return render_template("login.html")

@app.route("/")
def home():
    if not session.get("autenticado"):
        return redirect(url_for("login"))
    return render_template("index.html", nombre=session.get("nombre"))

@app.route("/api/carrera/iniciar", methods=["POST"])
def iniciar_carrera():
    if not session.get("autenticado"): return _no_autenticado()
    try:
        estado = servicio.iniciar()
    except CarreraYaActivaError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"mensaje": "Carrera iniciada", "estado": estado})

@app.route("/api/carrera/estado", methods=["POST"])
def cambiar_estado():
    if not session.get("autenticado"): return _no_autenticado()
    try:
        estado = servicio.alternar_estado()
    except SinCarreraActivaError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"mensaje": "Estado cambiado", "estado": estado})

@app.route("/api/carrera/finalizar", methods=["POST"])
def finalizar_carrera():
    if not session.get("autenticado"): return _no_autenticado()
    try:
        total = servicio.finalizar()
    except SinCarreraActivaError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"mensaje": "Carrera finalizada", "total": total})

@app.route("/api/carrera/actual", methods=["GET"])
def carrera_actual():
    if not session.get("autenticado"): return _no_autenticado()
    return jsonify(servicio.estado_actual())

@app.route("/api/historial", methods=["GET"])
def ver_historial():
    if not session.get("autenticado"): return _no_autenticado()
    return jsonify(servicio.historial_del_dia())

@app.route("/logout")
def logout():
    logger.info(f"Usuario {session.get('nombre')} ha cerrado sesión.")
    session.pop("autenticado", None)
    session.pop("nombre", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    # El modo debug (recarga automática y consola interactiva) solo se activa a propósito.
    debug = os.environ.get("TAXITECH_DEBUG") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
