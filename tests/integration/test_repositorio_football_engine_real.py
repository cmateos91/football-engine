from __future__ import annotations

import pytest

from motor_futbol.compartido.configuracion import cargar_configuracion
from motor_futbol.datos import VERSION_MAPEO_FOOTBALL_ENGINE, RepositorioFootballEngine
from motor_futbol.dominio import PosicionJugador


def test_repositorio_carga_equipos_y_jugadores_reales() -> None:
    configuracion = cargar_configuracion()

    if not configuracion.base_de_datos_configurada:
        pytest.skip("No hay URL_BD configurada para pruebas de integracion reales.")

    repositorio = RepositorioFootballEngine.desde_configuracion(configuracion)

    equipos = repositorio.listar_equipos_crudos()
    barcelona = repositorio.obtener_equipo_por_id(149)

    assert repositorio.version_mapeo == VERSION_MAPEO_FOOTBALL_ENGINE
    assert len(equipos) == 20
    assert barcelona.nombre == "FC Barcelona"
    assert barcelona.total_jugadores > 0
    assert all(jugador.id_equipo == barcelona.id for jugador in barcelona.jugadores)
    assert any(jugador.posicion is PosicionJugador.PORTERO for jugador in barcelona.jugadores)


def test_repositorio_busca_equipo_por_nombre() -> None:
    configuracion = cargar_configuracion()

    if not configuracion.base_de_datos_configurada:
        pytest.skip("No hay URL_BD configurada para pruebas de integracion reales.")

    repositorio = RepositorioFootballEngine.desde_configuracion(configuracion)
    equipo = repositorio.obtener_equipo_por_nombre("Real Madrid")

    assert equipo.id == 154
    assert equipo.total_jugadores > 0
