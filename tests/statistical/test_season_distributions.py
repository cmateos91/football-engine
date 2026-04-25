"""Tests de distribución de temporada vs SEASON_TARGETS de LaLiga.

Fuente: docs/calibration/CALIBRATION_TARGETS.md, secciones 5 y 6.
Fase: 10 (simulación de temporada completa).

Estado actual: los tests de SEASON_TARGETS requieren 20 equipos con plantillas
reales o sintéticas de diferente nivel. La función simular_temporada existe pero
los equipos por defecto carecen de jugadores reales asignados. Se marcan como
skip hasta que se resuelva la configuración de plantillas de temporada.
"""

from __future__ import annotations

import pytest
from tests.statistical.conftest import assert_target

from motor_futbol.calibracion import HISTORICAL_RANGES, HISTORICAL_SEASONS, SEASON_TARGETS

# ── Helper ───────────────────────────────────────────────────────────────────


def _simular_una_temporada(semilla: int = 2025):
    from motor_futbol.simulacion.temporada import simular_temporada
    from tests.unit.fabrica_dominio import crear_equipo_con_nivel

    equipos = []
    # Replicar curva de LaLiga
    niveles = [88, 86, 81, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 70, 69, 68, 68, 67, 66, 65]
    for i in range(1, 21):
        nivel = niveles[i - 1]
        equipos.append(crear_equipo_con_nivel(id_equipo=i, nombre=f"Equipo {i}", nivel_general=nivel))

    return simular_temporada(equipos=equipos, semilla=semilla)


# ── Tests SEASON_TARGETS ──────────────────────────────────────────────────────



def test_puntos_campeon() -> None:
    resultado = _simular_una_temporada()
    puntos_campeon = resultado.clasificacion[0].puntos
    assert_target(float(puntos_campeon), SEASON_TARGETS["champion_points"], "champion_points")



def test_puntos_descenso_18() -> None:
    resultado = _simular_una_temporada()
    puntos_18 = resultado.clasificacion[17].puntos
    assert_target(float(puntos_18), SEASON_TARGETS["relegation_pts_18th"], "relegation_pts_18th")



def test_goles_totales_temporada() -> None:
    resultado = _simular_una_temporada()
    total_goles = (
        sum(eq.goles_favor for eq in resultado.estadisticas_equipos.values()) // 2
    )  # cada gol se cuenta dos veces (favor + contra)
    # Ajuste: suma de goles_favor = goles totales del torneo (sin dividir)
    total_goles = sum(eq.goles_favor for eq in resultado.estadisticas_equipos.values())
    assert_target(
        float(total_goles),
        SEASON_TARGETS["total_league_goals"],
        "total_league_goals",
    )



def test_equipos_con_mas_de_60_puntos() -> None:
    resultado = _simular_una_temporada()
    equipos_60 = sum(1 for c in resultado.clasificacion if c.puntos > 60)
    target = SEASON_TARGETS["teams_over_60_pts"]
    lo, hi = target["range"]
    assert lo <= equipos_60 <= hi, f"teams_over_60={equipos_60} fuera de [{lo}, {hi}]"



def test_reproducibilidad_temporada() -> None:
    r1 = _simular_una_temporada(semilla=2025)
    r2 = _simular_una_temporada(semilla=2025)
    assert r1.clasificacion[0].equipo_id == r2.clasificacion[0].equipo_id
    assert r1.clasificacion[0].puntos == r2.clasificacion[0].puntos


# ── Validación histórica (Fase 12) ────────────────────────────────────────────


@pytest.mark.skip(reason="Fase 12 pendiente: validación cruzada temporal no implementada")
def test_historical_ranges_consistency() -> None:
    """Verifica que los rangos históricos internos son consistentes con los datos."""
    for season in HISTORICAL_SEASONS:
        gpm = season["goals_per_match"]
        lo = HISTORICAL_RANGES["goals_per_match"]["min"]
        hi = HISTORICAL_RANGES["goals_per_match"]["max"]
        assert lo <= gpm <= hi, (
            f"Temporada {season['season']}: gpm={gpm} fuera de rango [{lo}, {hi}]"
        )
