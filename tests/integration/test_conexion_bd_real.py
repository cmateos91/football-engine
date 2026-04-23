from __future__ import annotations

import pytest

from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos.conexion_bd import inspeccionar_estado_basico_bd


def test_conexion_real_a_football_engine() -> None:
    configuracion = cargar_configuracion()

    if not configuracion.base_de_datos_configurada:
        pytest.skip("No hay URL_BD configurada para pruebas de integracion reales.")

    estado = inspeccionar_estado_basico_bd(configuracion)

    assert estado.nombre_bd == "football_engine"
    assert "Equipo" in estado.tablas
    assert "Jugador" in estado.tablas
    assert estado.total_equipos == 20
    assert estado.total_jugadores > 0
