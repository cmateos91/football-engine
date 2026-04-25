"""Tests de distribución de eventos — GOAL_TIMING_TARGETS y GOAL_TYPE_TARGETS.

Fuente: docs/calibration/CALIBRATION_TARGETS.md, secciones 2 y 3.
Fase: 7 (motor de eventos avanzado).
"""

from __future__ import annotations

import pytest
from tests.statistical.conftest import assert_target

from motor_futbol.calibracion import GOAL_TIMING_TARGETS, GOAL_TYPE_TARGETS
from motor_futbol.dominio import TipoEventoPartido
from motor_futbol.simulacion.modelos import ResultadoSimulacionPartido

# ── Distribución temporal de goles ───────────────────────────────────────────


def _distribucion_temporal(rs: list[ResultadoSimulacionPartido]) -> dict[str, float]:
    """Fracción de goles por tramo de 15 minutos."""
    conteos: dict[str, int] = dict.fromkeys(GOAL_TIMING_TARGETS, 0)
    total = 0
    for r in rs:
        for e in r.estado_final.eventos:
            if e.tipo is not TipoEventoPartido.GOL:
                continue
            total += 1
            m = e.minuto
            if m <= 15:
                conteos["0_15"] += 1
            elif m <= 30:
                conteos["16_30"] += 1
            elif m <= 45:
                conteos["31_45"] += 1
            elif m <= 60:
                conteos["46_60"] += 1
            elif m <= 75:
                conteos["61_75"] += 1
            elif m <= 90:
                conteos["76_90"] += 1
            else:
                conteos["90+"] += 1
    if total == 0:
        return dict.fromkeys(conteos, 0.0)
    return {k: v / total for k, v in conteos.items()}


@pytest.mark.parametrize("tramo", list(GOAL_TIMING_TARGETS.keys()))
def test_distribucion_goles_por_tramo(
    tramo: str,
    partidos_simetricos_500: list[ResultadoSimulacionPartido],
) -> None:
    dist = _distribucion_temporal(partidos_simetricos_500)
    fraccion = dist.get(tramo, 0.0)
    assert_target(fraccion, GOAL_TIMING_TARGETS[tramo], f"goal_timing[{tramo}]")


# ── Tipos de gol ──────────────────────────────────────────────────────────────
# Requiere que los eventos de gol tengan metadato "tipo_gol".
# El motor baseline actual NO registra este metadato → tests marcados xfail.
# Se deben activar cuando el motor registre el contexto de cada gol.


def _distribucion_tipos(rs: list[ResultadoSimulacionPartido]) -> dict[str, float]:
    conteos: dict[str, int] = dict.fromkeys(GOAL_TYPE_TARGETS, 0)
    total = 0
    for r in rs:
        for e in r.estado_final.eventos:
            if e.tipo is not TipoEventoPartido.GOL:
                continue
            total += 1
            tipo_gol = e.metadatos.get("tipo_gol", "open_play")
            if tipo_gol in conteos:
                conteos[tipo_gol] += 1
            else:
                conteos["open_play"] += 1
    if total == 0:
        return dict.fromkeys(conteos, 0.0)
    return {k: v / total for k, v in conteos.items()}


@pytest.mark.parametrize("tipo", list(GOAL_TYPE_TARGETS.keys()))
def test_distribucion_tipos_gol(
    tipo: str,
    partidos_simetricos_500: list[ResultadoSimulacionPartido],
) -> None:
    dist = _distribucion_tipos(partidos_simetricos_500)
    fraccion = dist.get(tipo, 0.0)
    assert_target(fraccion, GOAL_TYPE_TARGETS[tipo], f"goal_type[{tipo}]")
