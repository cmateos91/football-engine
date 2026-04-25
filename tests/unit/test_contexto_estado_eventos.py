from __future__ import annotations

import pytest
from tests.unit.fabrica_dominio import crear_contexto_partido, crear_equipo

from motor_futbol.dominio import (
    ContextoPartido,
    EstadoPartido,
    EventoPartido,
    FasePartido,
    TipoEventoPartido,
)


def test_contexto_partido_valido_hace_roundtrip() -> None:
    contexto = crear_contexto_partido()

    restaurado = ContextoPartido.desde_dict(contexto.a_dict())

    assert restaurado == contexto


def test_contexto_partido_rechaza_equipos_duplicados() -> None:
    equipo = crear_equipo(1, "Duplicado FC")
    with pytest.raises(ValueError, match="distintos"):
        ContextoPartido(
            competicion="LaLiga",
            temporada="2025-2026",
            equipo_local=equipo,
            equipo_visitante=equipo,
        )


def test_evento_gol_exige_equipo_y_jugador() -> None:
    with pytest.raises(ValueError, match="requiere equipo_id"):
        EventoPartido(tipo=TipoEventoPartido.GOL, minuto=12)


def test_estado_partido_rechaza_eventos_del_futuro() -> None:
    evento = EventoPartido(
        tipo=TipoEventoPartido.GOL,
        minuto=35,
        equipo_id=1,
        jugador_principal_id=9,
    )

    with pytest.raises(ValueError, match="posteriores"):
        EstadoPartido(fase=FasePartido.PRIMER_TIEMPO, minuto=20, eventos=(evento,))


def test_estado_partido_hace_roundtrip_y_expone_marcador() -> None:
    evento = EventoPartido(
        tipo=TipoEventoPartido.GOL,
        minuto=18,
        equipo_id=1,
        jugador_principal_id=9,
        descripcion="Gol de cabeza",
        metadatos={"tipo_remate": "cabeza"},
    )
    estado = EstadoPartido(
        fase=FasePartido.PRIMER_TIEMPO,
        minuto=20,
        goles_local=1,
        goles_visitante=0,
        posesion_equipo_id=1,
        eventos=(evento,),
    )

    restaurado = EstadoPartido.desde_dict(estado.a_dict())

    assert restaurado == estado
    assert restaurado.marcador == "1-0"
