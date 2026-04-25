from __future__ import annotations

import pytest

from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos import inspeccionar_esquema_bd, obtener_columnas_esperadas


def test_esquema_real_coincide_con_el_catalogo_de_mapeo() -> None:
    configuracion = cargar_configuracion()

    if not configuracion.base_de_datos_configurada:
        pytest.skip("No hay URL_BD configurada para pruebas de integracion reales.")

    inventario = inspeccionar_esquema_bd(configuracion)
    tabla_equipo = inventario.obtener_tabla("Equipo")
    tabla_jugador = inventario.obtener_tabla("Jugador")

    assert inventario.nombre_bd == "football_engine"
    assert set(tabla_equipo.nombres_columnas) == set(obtener_columnas_esperadas("Equipo"))
    assert set(tabla_jugador.nombres_columnas) == set(obtener_columnas_esperadas("Jugador"))
    assert tabla_jugador.obtener_columna("altura").admite_nulos is True
    assert tabla_jugador.obtener_columna("overall").admite_nulos is False
