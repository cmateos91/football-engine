"""Tests de validación de tácticas del motor."""

from __future__ import annotations

import random

from tests.unit.fabrica_dominio import crear_equipo_con_nivel, crear_suplentes, crear_titulares

from motor_futbol.dominio import (
    Alineacion,
    ContextoPartido,
    EstiloPresion,
    MentalidadTactica,
    Tactica,
)
from motor_futbol.simulacion import simular_partido_baseline


def _crear_tactica(
    mentalidad: MentalidadTactica = MentalidadTactica.EQUILIBRADA,
    presion: EstiloPresion = EstiloPresion.MEDIA,
    ritmo: int = 50,
    agresividad: int = 50,
) -> Tactica:
    return Tactica(
        nombre="Test",
        formacion="4-3-3",
        mentalidad=mentalidad,
        presion=presion,
        ritmo=ritmo,
        agresividad=agresividad,
    )


def _crear_alineacion(id_eq: int, tactica: Tactica) -> Alineacion:
    return Alineacion(
        id_equipo=id_eq,
        tactica=tactica,
        titulares=crear_titulares(id_eq),
        suplentes=crear_suplentes(id_eq),
    )


def test_tactica_ofensiva_vs_defensiva() -> None:
    tactica_ofensiva = _crear_tactica(mentalidad=MentalidadTactica.OFENSIVA)
    tactica_defensiva = _crear_tactica(mentalidad=MentalidadTactica.DEFENSIVA)
    eq = crear_equipo_con_nivel(id_equipo=1, nombre="Eq", nivel_general=75)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=75)

    ofensiva = _crear_alineacion(1, tactica_ofensiva)
    defensiva = _crear_alineacion(2, tactica_defensiva)

    random.seed(42)
    resul = [
        simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq,
                equipo_visitante=eq2,
                alineacion_local=ofensiva,
                alineacion_visitante=defensiva,
                semilla=random.randint(1, 10000),
            )
        )
        for _ in range(20)
    ]

    tires = sum(r.estadisticas_local.tiros + r.estadisticas_visitante.tiros for r in resul)
    assert tires > 0, f"Tiros debe ser > 0, got {tires}"


def test_presion_alta_vs_baja() -> None:
    tactica_alta = _crear_tactica(presion=EstiloPresion.ALTA)
    tactica_baja = _crear_tactica(presion=EstiloPresion.BAJA)
    eq = crear_equipo_con_nivel(id_equipo=1, nombre="Eq", nivel_general=75)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=75)

    alta = _crear_alineacion(1, tactica_alta)
    baja = _crear_alineacion(2, tactica_baja)

    random.seed(42)
    resul = [
        simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq,
                equipo_visitante=eq2,
                alineacion_local=alta,
                alineacion_visitante=baja,
                semilla=random.randint(1, 10000),
            )
        )
        for _ in range(20)
    ]

    faltas = sum(r.estadisticas_local.faltas + r.estadisticas_visitante.faltas for r in resul)
    assert faltas > 0, f"Faltas debe ser > 0, got {faltas}"


def test_ritmo_alto_da_mas_tiros() -> None:
    tactica_rapida = _crear_tactica(ritmo=85)
    tactica_lenta = _crear_tactica(ritmo=20)
    eq = crear_equipo_con_nivel(id_equipo=1, nombre="Eq", nivel_general=75)
    eq2 = crear_equipo_con_nivel(id_equipo=2, nombre="Eq2", nivel_general=75)

    rapida = _crear_alineacion(1, tactica_rapida)
    lenta = _crear_alineacion(2, tactica_lenta)

    random.seed(42)
    resul = [
        simular_partido_baseline(
            ContextoPartido(
                competicion="Test",
                temporada="2025",
                equipo_local=eq,
                equipo_visitante=eq2,
                alineacion_local=rapida,
                alineacion_visitante=lenta,
                semilla=random.randint(1, 10000),
            )
        )
        for _ in range(20)
    ]

    tiros = sum(r.total_tiros for r in resul)
    assert tiros > 0, f"Tiros debe ser > 0, got {tiros}"
