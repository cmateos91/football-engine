"""Verificación de invariantes duros del motor — HARD_INVARIANTS.

Estos tests deben pasar siempre, en cualquier simulación, con cualquier seed.
Fuente: docs/calibration/CALIBRATION_TARGETS.md, sección 7.
"""

from __future__ import annotations

import random

from tests.unit.fabrica_dominio import (
    crear_contexto_baseline_desde_equipos,
    crear_equipo_con_nivel,
)

from motor_futbol.dominio import TipoEventoPartido
from motor_futbol.simulacion import simular_partido_baseline
from motor_futbol.simulacion.modelos import ResultadoSimulacionPartido


def _partidos(n: int, semilla_base: int = 9999) -> list[ResultadoSimulacionPartido]:
    eq_a = crear_equipo_con_nivel(id_equipo=1, nombre="A", nivel_general=75)
    eq_b = crear_equipo_con_nivel(id_equipo=2, nombre="B", nivel_general=75)
    random.seed(semilla_base)
    seeds = [random.randint(1, 100_000) for _ in range(n)]
    return [
        simular_partido_baseline(crear_contexto_baseline_desde_equipos(eq_a, eq_b, semilla=s))
        for s in seeds
    ]


# ── INV-001: Goles >= 0 ───────────────────────────────────────────────────────


def test_inv001_goles_no_negativos() -> None:
    for r in _partidos(200):
        assert r.estadisticas_local.goles >= 0, "INV-001: local goles < 0"
        assert r.estadisticas_visitante.goles >= 0, "INV-001: visit goles < 0"


# ── INV-002: SOT <= tiros totales ──────────────────────────────��──────────────


def test_inv002_sot_menor_o_igual_que_tiros() -> None:
    for r in _partidos(200):
        assert r.estadisticas_local.tiros_a_puerta <= r.estadisticas_local.tiros, (
            "INV-002: local SOT "
            f"{r.estadisticas_local.tiros_a_puerta} > tiros {r.estadisticas_local.tiros}"
        )
        assert r.estadisticas_visitante.tiros_a_puerta <= r.estadisticas_visitante.tiros, (
            "INV-002: visit SOT "
            f"{r.estadisticas_visitante.tiros_a_puerta} > tiros {r.estadisticas_visitante.tiros}"
        )


# ── INV-003: xG ∈ [0.001, 0.99] — verificado vía modelo xG directamente ──────
# (El motor baseline no expone xG por disparo en el resultado; el modelo se
#  valida en test_xg_model.py. Aquí sólo verificamos el rango del modelo.)


def test_inv003_xg_bounds_via_modelo() -> None:
    from motor_futbol.calibracion import XG_HARD_BOUNDS as TARGET_BOUNDS
    from motor_futbol.simulacion.xg import calcular_xg

    eq = crear_equipo_con_nivel(id_equipo=1, nombre="T", nivel_general=75)
    jugador = eq.jugadores[0]
    casos = [
        (99.0, 50.0),  # muy cerca, ángulo central
        (5.0, 50.0),  # muy lejos
        (80.0, 0.0),  # ángulo extremo
        (95.0, 25.0),  # cerca, ángulo abierto
    ]
    for pos in casos:
        for cabeza in (True, False):
            r = calcular_xg(jugador, pos, es_cabeza=cabeza)
            assert TARGET_BOUNDS[0] <= r.xg <= TARGET_BOUNDS[1], (
                f"INV-003: xG={r.xg:.4f} fuera de [{TARGET_BOUNDS[0]}, {TARGET_BOUNDS[1]}]"
                f" para pos={pos}, cabeza={cabeza}"
            )


# ── INV-004: Minutos ∈ [90, 100] ────────────────────────────��────────────────


def test_inv004_minutos_partido() -> None:
    for r in _partidos(100):
        minuto_final = r.estado_final.minuto
        assert 90 <= minuto_final <= 100, f"INV-004: minuto_final={minuto_final}"


# ── INV-005: Posesión local + visitante = 100 % ───────────────────────────���───


def test_inv005_posesion_suma_100() -> None:
    for r in _partidos(200):
        total = r.estadisticas_local.posesion_pct + r.estadisticas_visitante.posesion_pct
        assert round(total, 2) == 100.0, f"INV-005: posesion total = {total:.3f} ≠ 100"


# ── INV-006: Resultado consistente con log de goles ──────────────────────────


def test_inv006_resultado_consistente_con_log() -> None:
    for r in _partidos(200):
        goles_local_log = sum(
            1
            for e in r.estado_final.eventos
            if e.tipo is TipoEventoPartido.GOL and e.equipo_id == r.contexto.equipo_local.id
        )
        goles_visit_log = sum(
            1
            for e in r.estado_final.eventos
            if e.tipo is TipoEventoPartido.GOL and e.equipo_id == r.contexto.equipo_visitante.id
        )
        assert goles_local_log == r.estadisticas_local.goles, (
            f"INV-006: log_local={goles_local_log} ≠ stats_local={r.estadisticas_local.goles}"
        )
        assert goles_visit_log == r.estadisticas_visitante.goles, (
            f"INV-006: log_visit={goles_visit_log} ≠ stats_visit={r.estadisticas_visitante.goles}"
        )


# ── INV-007: Seed fija produce resultado idéntico ────────────────────────────


def test_inv007_reproducibilidad_por_seed() -> None:
    eq_a = crear_equipo_con_nivel(id_equipo=1, nombre="A", nivel_general=75)
    eq_b = crear_equipo_con_nivel(id_equipo=2, nombre="B", nivel_general=75)
    ctx = crear_contexto_baseline_desde_equipos(eq_a, eq_b, semilla=42)
    r1 = simular_partido_baseline(ctx)
    r2 = simular_partido_baseline(ctx)
    assert r1.estadisticas_local.goles == r2.estadisticas_local.goles
    assert r1.estadisticas_visitante.goles == r2.estadisticas_visitante.goles
    assert r1.total_tiros == r2.total_tiros
    assert len(r1.estado_final.eventos) == len(r2.estado_final.eventos)
