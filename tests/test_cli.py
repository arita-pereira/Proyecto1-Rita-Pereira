import pytest

import src.interfaces.cli as cli
from src.infrastructure.auth import ConfiguracionSeguridadError


def test_cli_sin_contrasena_configurada_sale_con_mensaje(monkeypatch, capsys):
    def sin_fichero():
        raise ConfiguracionSeguridadError("No existe config/security.json.")

    monkeypatch.setattr(cli, "cargar_registro", sin_fichero)
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("No debería pedir datos"))

    with pytest.raises(SystemExit) as salida:
        cli.main()

    assert salida.value.code == 1
    assert "No existe config/security.json." in capsys.readouterr().out
