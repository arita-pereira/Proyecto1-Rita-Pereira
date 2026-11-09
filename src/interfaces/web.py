from flask import Flask, jsonify, request, redirect, url_for, render_template, session
import os
import secrets
from src.domain.carrera import Carrera
from src.interfaces.cli import cargar_tarifa
from src.infrastructure.historial import guardar_carrera, obtener_historial_dia
from src.infrastructure.auth import verificar_password
from src.infrastructure.logger import configurar_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

tarifa = cargar_tarifa()
logger = configurar_logger()

# La clave que firma la cookie de sesión no se guarda en el código: si estuviera en el
# repositorio, cualquiera podría falsificar una sesión autenticada.
clave_secreta = os.environ.get("TAXITECH_SECRET_KEY")
if not clave_secreta:
    clave_secreta = secrets.token_hex(32)
    logger.warning("TAXITECH_SECRET_KEY no definida: se usa una clave aleatoria "
                   "y las sesiones se cerrarán al reiniciar el servidor.")
app.secret_key = clave_secreta

logger.info("Aplicación web iniciada.")
carrera_activa = None

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
    if not session.get("autenticado"): return jsonify({"error": "No autenticado"}), 401
    global carrera_activa
    if carrera_activa is not None:
        return jsonify({"error": "Ya hay una carrera en curso."}), 400
    else:
        carrera_activa = Carrera()
        logger.info("Carrera iniciada.")
        return jsonify({"mensaje": "Carrera iniciada", "estado": carrera_activa.estado_actual})

@app.route("/api/carrera/estado", methods=["POST"])
def cambiar_estado():
    if not session.get("autenticado"): return jsonify({"error": "No autenticado"}), 401
    global carrera_activa
    if carrera_activa is None:
        return jsonify({"error": "No hay ninguna carrera activa."}), 400
    else:
        nuevo_estado = "movimiento" if carrera_activa.estado_actual == "parado" else "parado"
        carrera_activa.cambiar_estado(nuevo_estado)
        logger.info(f"Estado de la carrera cambiado a {nuevo_estado}.")
        return jsonify({"mensaje": "Estado cambiado", "estado": nuevo_estado})

@app.route("/api/carrera/finalizar", methods=["POST"])
def finalizar_carrera():
    if not session.get("autenticado"): return jsonify({"error": "No autenticado"}), 401
    global carrera_activa
    if carrera_activa is None:
        return jsonify({"error": "No hay ninguna carrera activa."}), 400
    else:
        carrera_activa.finalizar_carrera()
        total = carrera_activa.calcular_total(tarifa)
        guardar_carrera(carrera_activa, tarifa)
        carrera_activa = None
        logger.info(f"Carrera finalizada. Total: {round(total, 2)}")
        return jsonify({"mensaje": "Carrera finalizada", "total": round(total, 2)})

@app.route("/api/carrera/actual", methods=["GET"])
def carrera_actual():
    if not session.get("autenticado"): return jsonify({"error": "No autenticado"}), 401
    if carrera_activa is None:
        return jsonify({"activa": False})
    else:
        return jsonify({"activa": True, "estado": carrera_activa.estado_actual, "total": round(carrera_activa.total_actual(tarifa), 2)})

@app.route("/api/historial", methods=["GET"])
def ver_historial():
    if not session.get("autenticado"): return jsonify({"error": "No autenticado"}), 401
    historial = obtener_historial_dia()
    return jsonify(historial)

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