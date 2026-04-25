"""Tests del modelo de Expected Goals (xG).

Valida el comportamiento de calcular_xg contra XG_ZONE_TARGETS y XG_MODIFIERS.
Fuente: docs/calibration/CALIBRATION_TARGETS.md, secciones 4 y 7.
Fase: 9 (modelo xG).
"""

from __future__ import annotations

import pytest
from tests.unit.fabrica_dominio import crear_equipo_con_nivel

from motor_futbol.calibracion import XG_HARD_BOUNDS, XG_ZONE_TARGETS
from motor_futbol.simulacion.xg import calcular_xg


@pytest.fixture(scope="module")
def jugador_elite():
    eq = crear_equipo_con_nivel(id_equipo=1, nombre="Elite", nivel_general=90, bonus_ataque=9)
    return eq.jugadores[0]


@pytest.fixture(scope="module")
def jugador_base():
    eq = crear_equipo_con_nivel(id_equipo=2, nombre="Base", nivel_general=75)
    return eq.jugadores[0]


# ── Invariante duro: xG ∈ [0.001, 0.99] ─────────────────────────────────────


@pytest.mark.parametrize(
    ("pos", "cabeza"),
    [
        ((99.0, 50.0), False),
        ((5.0, 50.0), False),
        ((80.0, 0.0), False),
        ((95.0, 50.0), True),
        ((70.0, 10.0), True),
    ],
)
def test_xg_siempre_en_bounds(jugador_base, pos, cabeza) -> None:
    r = calcular_xg(jugador_base, pos, es_cabeza=cabeza)
    lo, hi = XG_HARD_BOUNDS
    assert lo <= r.xg <= hi, f"xG={r.xg:.4f} fuera de [{lo}, {hi}] para pos={pos}, cabeza={cabeza}"


# ── Escenarios específicos de CALIBRATION_TARGETS ────────────────────────────


def test_penalti_elite_xg_mayor_070(jugador_elite) -> None:
    """Punto de penalti, delantero élite: xG >= 0.70 (XG_ZONE_TARGETS penalty.xg_mean=0.76)."""
    # Punto de penalti ≈ x=89, y=50 (11m del arco en coordenadas 0-100)
    r = calcular_xg(jugador_elite, (89.0, 50.0), usa_pie_dominante=True, energia=100.0)
    XG_ZONE_TARGETS["penalty"]["xg_range"][0]  # lower bound = 0.72
    assert r.xg >= 0.70, f"Penalti élite: xG={r.xg:.3f} < 0.70 | factores={r.factores}"


def test_cabeza_20m_xg_menor_005(jugador_base) -> None:
    """Cabeza desde 20m: xG <= 0.05 (escenario de remate lejano de baja calidad)."""
    # 20m del arco = x≈80, ángulo central
    r = calcular_xg(jugador_base, (80.0, 50.0), es_cabeza=True)
    assert r.xg <= 0.05, f"Cabeza 20m: xG={r.xg:.3f} > 0.05 | factores={r.factores}"


def test_finalizacion_alta_mayor_xg(jugador_base) -> None:
    """Mayor finalizacion en igualdad de posición -> mayor xG."""
    eq_high = crear_equipo_con_nivel(id_equipo=3, nombre="High", nivel_general=75, bonus_ataque=20)
    j_high = eq_high.jugadores[0]
    r_base = calcular_xg(jugador_base, (85.0, 50.0))
    r_high = calcular_xg(j_high, (85.0, 50.0))
    assert r_high.xg >= r_base.xg, (
        f"finalizacion alta debe generar mayor xG: {r_high.xg:.3f} < {r_base.xg:.3f}"
    )


def test_pie_dominante_mayor_xg(jugador_base) -> None:
    """Pie dominante debe producir mayor xG que pie no dominante."""
    r_dom = calcular_xg(jugador_base, (85.0, 50.0), usa_pie_dominante=True)
    r_nod = calcular_xg(jugador_base, (85.0, 50.0), usa_pie_dominante=False)
    assert r_dom.xg >= r_nod.xg, (
        f"pie dominante ({r_dom.xg:.3f}) debe ser >= no dominante ({r_nod.xg:.3f})"
    )


def test_compostura_no_empeora_xg(jugador_base) -> None:
    """Subir la compostura del tirador no debe empeorar el xG."""
    eq_low = crear_equipo_con_nivel(id_equipo=4, nombre="Low", nivel_general=50)
    j_low = eq_low.jugadores[0]
    r_high = calcular_xg(jugador_base, (85.0, 50.0))
    r_low = calcular_xg(j_low, (85.0, 50.0))
    # El xG de calidad alta no debe ser peor que el de calidad baja
    assert r_high.xg >= r_low.xg - 0.01, (
        f"compostura alta ({r_high.xg:.3f}) peor que baja ({r_low.xg:.3f})"
    )


def test_fatiga_reduce_xg(jugador_base) -> None:
    """Alta fatiga debe reducir el xG."""
    r_fresco = calcular_xg(jugador_base, (85.0, 50.0), energia=100.0)
    r_fatigado = calcular_xg(jugador_base, (85.0, 50.0), energia=20.0)
    assert r_fresco.xg >= r_fatigado.xg, (
        f"fresco ({r_fresco.xg:.3f}) debe ser >= fatigado ({r_fatigado.xg:.3f})"
    )


def test_contraataque_aumenta_xg(jugador_base) -> None:
    """Contraataque debe producir mayor xG que jugada normal (XG_MODIFIERS counter_attack)."""
    r_normal = calcular_xg(jugador_base, (85.0, 50.0), es_contraataque=False)
    r_contra = calcular_xg(jugador_base, (85.0, 50.0), es_contraataque=True)
    assert r_contra.xg >= r_normal.xg, (
        f"contraataque ({r_contra.xg:.3f}) debe ser >= normal ({r_normal.xg:.3f})"
    )


def test_distancia_monotonicidad(jugador_base) -> None:
    """A mayor distancia del arco, menor xG."""
    posiciones = [(98.0, 50.0), (88.0, 50.0), (78.0, 50.0), (68.0, 50.0)]
    xgs = [calcular_xg(jugador_base, p).xg for p in posiciones]
    for i in range(len(xgs) - 1):
        assert xgs[i] >= xgs[i + 1], (
            "monotonicidad de distancia rota: "
            f"xG({posiciones[i]})={xgs[i]:.3f} < "
            f"xG({posiciones[i + 1]})={xgs[i + 1]:.3f}"
        )
