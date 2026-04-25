"""Tests de eventos avanzados del motor."""

from __future__ import annotations

import random

from tests.unit.fabrica_dominio import crear_equipo_con_nivel

from motor_futbol.dominio import ContextoPartido
from motor_futbol.simulacion import simular_partido_baseline


def test_contraataques_ocurren() -> None:
    eq1 = crear_equipo_con_nivel(id_equipo=1, nombre="Eq1", nivel_general=75)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=75)

    contraataques = 0
    random.seed(42)
    for _ in range(50):
        resultado = simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq1,
                equipo_visitante=eq2,
                semilla=random.randint(1, 10000),
            )
        )
        for evento in resultado.estado_final.eventos:
            if evento.tipo.value == "Contraataque":
                contraataques += 1
                break

    assert contraataques > 0, f"Contraataques: {contraataques}"


def test_variacion_eventos() -> None:
    eq1 = crear_equipo_con_nivel(id_equipo=1, nombre="Eq1", nivel_general=75)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=75)

    tipos_eventos = set()
    random.seed(99)
    for _ in range(20):
        resultado = simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq1,
                equipo_visitante=eq2,
                semilla=random.randint(1, 10000),
            )
        )
        for evento in resultado.estado_final.eventos:
            tipos_eventos.add(evento.tipo.value)

    assert len(tipos_eventos) >= 5, f"Tipos de eventos: {tipos_eventos}"


def test_goles_se_registran() -> None:
    eq1 = crear_equipo_con_nivel(id_equipo=1, nombre="Eq1", nivel_general=80, bonus_ataque=15)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=65, bonus_ataque=-15)

    total_goles = 0
    random.seed(111)
    for _ in range(30):
        resultado = simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq1,
                equipo_visitante=eq2,
                semilla=random.randint(1, 10000),
            )
        )
        total_goles += resultado.total_goles

    assert total_goles > 0, f"Goles totales: {total_goles}"
