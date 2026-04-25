from __future__ import annotations

import pytest
from tests.unit.fabrica_dominio import crear_jugador

from motor_futbol.dominio import Equipo, PosicionJugador
from motor_futbol.simulacion import SeleccionAlineacionError, construir_alineacion_baseline


def test_selector_baseline_construye_once_valido() -> None:
    equipo = Equipo(
        id=1,
        nombre="Equipo Selector",
        jugadores=tuple(
            crear_jugador(id_jugador=100 + indice, id_equipo=1, posicion=posicion)
            for indice, posicion in enumerate(
                (
                    PosicionJugador.PORTERO,
                    PosicionJugador.CENTRAL,
                    PosicionJugador.CENTRAL,
                    PosicionJugador.LATERAL,
                    PosicionJugador.LATERAL,
                    PosicionJugador.MEDIOCENTRO,
                    PosicionJugador.MEDIOCENTRO,
                    PosicionJugador.MEDIAPUNTA,
                    PosicionJugador.EXTREMO,
                    PosicionJugador.EXTREMO,
                    PosicionJugador.DELANTERO,
                    PosicionJugador.DELANTERO,
                )
            )
        ),
    )

    alineacion = construir_alineacion_baseline(equipo)

    assert len(alineacion.titulares) == 11
    assert sum(1 for jugador in alineacion.titulares if jugador.es_portero) == 1
    assert alineacion.tactica.formacion == "4-3-3"


def test_selector_falla_si_no_hay_portero() -> None:
    equipo = Equipo(
        id=2,
        nombre="Sin Portero",
        jugadores=tuple(
            crear_jugador(id_jugador=200 + indice, id_equipo=2, posicion=PosicionJugador.CENTRAL)
            for indice in range(11)
        ),
    )

    with pytest.raises(SeleccionAlineacionError, match="porteros"):
        construir_alineacion_baseline(equipo)
