import pytest

from tests.conftest import PASSWORD_TEST


# --- Acceso y sesión -------------------------------------------------------

def test_home_sin_sesion_redirige_a_login(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/login")


def test_login_correcto_abre_sesion(cliente):
    respuesta = cliente.post("/login", data={"password": PASSWORD_TEST, "nombre": "Rita"})
    assert respuesta.status_code == 302
    with cliente.session_transaction() as sesion:
        assert sesion["autenticado"] is True
        assert sesion["nombre"] == "Rita"


def test_login_incorrecto_no_abre_sesion(cliente):
    respuesta = cliente.post("/login", data={"password": "equivocada", "nombre": "Rita"})
    assert respuesta.status_code == 200
    assert "Contraseña incorrecta" in respuesta.get_data(as_text=True)
    with cliente.session_transaction() as sesion:
        assert "autenticado" not in sesion


def test_home_con_sesion_responde_200(cliente_autenticado):
    assert cliente_autenticado.get("/").status_code == 200


def test_logout_cierra_la_sesion(cliente_autenticado):
    cliente_autenticado.get("/logout")
    assert cliente_autenticado.get("/api/historial").status_code == 401


@pytest.mark.parametrize("metodo, ruta", [
    ("post", "/api/carrera/iniciar"),
    ("post", "/api/carrera/estado"),
    ("post", "/api/carrera/finalizar"),
    ("get", "/api/carrera/actual"),
    ("get", "/api/historial"),
])
def test_endpoints_protegidos_devuelven_401_sin_sesion(cliente, metodo, ruta):
    respuesta = getattr(cliente, metodo)(ruta)
    assert respuesta.status_code == 401
    assert respuesta.get_json() == {"error": "No autenticado"}


# --- Carrera ---------------------------------------------------------------

def test_iniciar_carrera(cliente_autenticado, reloj):
    respuesta = cliente_autenticado.post("/api/carrera/iniciar")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "parado"


def test_no_se_puede_iniciar_otra_carrera_en_curso(cliente_autenticado, reloj):
    cliente_autenticado.post("/api/carrera/iniciar")
    respuesta = cliente_autenticado.post("/api/carrera/iniciar")
    assert respuesta.status_code == 400


def test_cambiar_estado_sin_carrera_activa(cliente_autenticado):
    assert cliente_autenticado.post("/api/carrera/estado").status_code == 400


def test_finalizar_sin_carrera_activa(cliente_autenticado):
    assert cliente_autenticado.post("/api/carrera/finalizar").status_code == 400


def test_cambiar_estado_alterna_parado_y_movimiento(cliente_autenticado, reloj):
    cliente_autenticado.post("/api/carrera/iniciar")
    primero = cliente_autenticado.post("/api/carrera/estado").get_json()
    segundo = cliente_autenticado.post("/api/carrera/estado").get_json()
    assert primero["estado"] == "movimiento"
    assert segundo["estado"] == "parado"


def test_carrera_actual_sin_carrera(cliente_autenticado):
    assert cliente_autenticado.get("/api/carrera/actual").get_json() == {"activa": False}


def test_carrera_actual_muestra_el_total_en_curso(cliente_autenticado, reloj):
    cliente_autenticado.post("/api/carrera/iniciar")
    reloj.avanzar(10)  # 10 s parado a 0.02 EUR/s
    datos = cliente_autenticado.get("/api/carrera/actual").get_json()
    assert datos["activa"] is True
    assert datos["estado"] == "parado"
    assert datos["total"] == pytest.approx(0.2)


def test_flujo_completo_calcula_el_total_y_guarda_el_historial(cliente_autenticado, reloj):
    cliente_autenticado.post("/api/carrera/iniciar")
    reloj.avanzar(10)                                    # 10 s parado   -> 0.20
    cliente_autenticado.post("/api/carrera/estado")      # pasa a movimiento
    reloj.avanzar(10)                                    # 10 s en marcha -> 0.50
    respuesta = cliente_autenticado.post("/api/carrera/finalizar")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["total"] == pytest.approx(0.7)
    assert cliente_autenticado.get("/api/carrera/actual").get_json() == {"activa": False}

    historial = cliente_autenticado.get("/api/historial").get_json()
    assert len(historial) == 1
    assert historial[0]["total"] == pytest.approx(0.7)


def test_se_pueden_encadenar_carreras(cliente_autenticado, reloj):
    for _ in range(2):
        cliente_autenticado.post("/api/carrera/iniciar")
        reloj.avanzar(5)
        cliente_autenticado.post("/api/carrera/finalizar")
    historial = cliente_autenticado.get("/api/historial").get_json()
    assert len(historial) == 2
