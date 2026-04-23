from __future__ import annotations

import pytest

from motor_futbol.compartido.configuracion import cargar_configuracion


def test_carga_valores_por_defecto() -> None:
    configuracion = cargar_configuracion(variables={})

    assert configuracion.entorno == "desarrollo"
    assert configuracion.nivel_log == "INFO"
    assert configuracion.semilla_por_defecto == 20260423
    assert configuracion.url_bd is None
    assert configuracion.base_de_datos_configurada is False


def test_carga_variables_explicitas() -> None:
    configuracion = cargar_configuracion(
        variables={
            "ENTORNO": "pruebas",
            "NIVEL_LOG": "debug",
            "SEMILLA_POR_DEFECTO": "99",
            "URL_BD": "mysql+pymysql://usuario:clave@localhost/laliga",
        }
    )

    assert configuracion.entorno == "pruebas"
    assert configuracion.nivel_log == "DEBUG"
    assert configuracion.semilla_por_defecto == 99
    assert configuracion.url_bd == "mysql+pymysql://usuario:clave@localhost/laliga"
    assert configuracion.base_de_datos_configurada is True


def test_semilla_invalida_lanza_error() -> None:
    with pytest.raises(ValueError, match="SEMILLA_POR_DEFECTO"):
        cargar_configuracion(variables={"SEMILLA_POR_DEFECTO": "no-es-un-entero"})
