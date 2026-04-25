from __future__ import annotations

from motor_futbol.datos import (
    VERSION_MAPEO_FOOTBALL_ENGINE,
    obtener_columnas_esperadas,
    obtener_definiciones_estadisticas_jugador,
    validar_catalogo_con_dominio,
)
from motor_futbol.dominio import AtributosJugador


def test_version_mapeo_tiene_prefijo_esperado() -> None:
    assert VERSION_MAPEO_FOOTBALL_ENGINE.startswith("football_engine.")


def test_catalogo_estadistico_cubre_todos_los_atributos_del_dominio() -> None:
    validar_catalogo_con_dominio()

    atributos_catalogados = {
        definicion.nombre_atributo
        for definicion in obtener_definiciones_estadisticas_jugador()
        if definicion.nombre_atributo is not None
    }

    assert atributos_catalogados == set(AtributosJugador.nombres_campos())


def test_columnas_esperadas_no_tienen_duplicados() -> None:
    columnas_equipo = obtener_columnas_esperadas("Equipo")
    columnas_jugador = obtener_columnas_esperadas("Jugador")

    assert len(columnas_equipo) == len(set(columnas_equipo))
    assert len(columnas_jugador) == len(set(columnas_jugador))
