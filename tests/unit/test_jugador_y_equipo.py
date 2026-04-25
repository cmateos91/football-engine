from __future__ import annotations

import pytest
from tests.unit.fabrica_dominio import crear_atributos, crear_equipo, crear_jugador

from motor_futbol.dominio import Equipo, Jugador, PosicionJugador


def test_jugador_valido_se_serializa_y_recupera() -> None:
    jugador = crear_jugador(
        id_jugador=7,
        id_equipo=1,
        nombre="Jugador Demo",
        posicion=PosicionJugador.DELANTERO,
        overall=84,
        atributos=crear_atributos(finalizacion=90, potencia_tiro=87),
    )

    restaurado = Jugador.desde_dict(jugador.a_dict())

    assert restaurado == jugador
    assert restaurado.es_portero is False


def test_jugador_invalido_por_nombre_vacio() -> None:
    with pytest.raises(ValueError, match="nombre"):
        crear_jugador(id_jugador=1, id_equipo=1, nombre="   ")


def test_equipo_rechaza_jugadores_duplicados() -> None:
    jugador = crear_jugador(id_jugador=10, id_equipo=1)
    with pytest.raises(ValueError, match="duplicados"):
        Equipo(id=1, nombre="Equipo X", jugadores=(jugador, jugador))


def test_equipo_rechaza_jugador_de_otro_equipo() -> None:
    jugador = crear_jugador(id_jugador=10, id_equipo=2)
    with pytest.raises(ValueError, match="no pertenece"):
        Equipo(id=1, nombre="Equipo X", jugadores=(jugador,))


def test_equipo_se_serializa_y_recupera() -> None:
    equipo = crear_equipo(1, "Equipo Serializado")

    restaurado = Equipo.desde_dict(equipo.a_dict())

    assert restaurado == equipo
    assert restaurado.total_jugadores == len(equipo.jugadores)
