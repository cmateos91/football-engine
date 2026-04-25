"""Suite de calibración — métricas de partido vs MATCH_TARGETS de LaLiga.

Fuente de targets: docs/calibration/CALIBRATION_TARGETS.md
Fase: 3 (goles, resultados), 4 (tiros, xG), 5 (posesión, eventos)
"""

from __future__ import annotations

from tests.statistical.conftest import assert_target

from motor_futbol.calibracion import MATCH_TARGETS
from motor_futbol.simulacion.modelos import ResultadoSimulacionPartido

# ── helpers ──────────────────────────────────────────────────────────────────


def _goles(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.total_goles for r in rs) / len(rs)


def _goles_local(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.estadisticas_local.goles for r in rs) / len(rs)


def _goles_visit(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.estadisticas_visitante.goles for r in rs) / len(rs)


def _tiros(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.total_tiros for r in rs) / len(rs)


def _sot(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(
        r.estadisticas_local.tiros_a_puerta + r.estadisticas_visitante.tiros_a_puerta for r in rs
    ) / len(rs)


def _sot_ratio(rs: list[ResultadoSimulacionPartido]) -> float:
    total_tiros = sum(r.total_tiros for r in rs)
    total_sot = sum(
        r.estadisticas_local.tiros_a_puerta + r.estadisticas_visitante.tiros_a_puerta for r in rs
    )
    return total_sot / total_tiros if total_tiros > 0 else 0.0


def _pos_local(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.estadisticas_local.posesion_pct for r in rs) / (len(rs) * 100.0)


def _corners(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.estadisticas_local.corners + r.estadisticas_visitante.corners for r in rs) / len(
        rs
    )


def _faltas(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(r.estadisticas_local.faltas + r.estadisticas_visitante.faltas for r in rs) / len(rs)


def _amarillas(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(
        r.estadisticas_local.tarjetas_amarillas + r.estadisticas_visitante.tarjetas_amarillas
        for r in rs
    ) / len(rs)


def _rojas(rs: list[ResultadoSimulacionPartido]) -> float:
    return sum(
        r.estadisticas_local.tarjetas_rojas + r.estadisticas_visitante.tarjetas_rojas for r in rs
    ) / len(rs)


# ── tests ─────────────────────────────────────────────────────────────────────


def test_goals_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(_goles(partidos_simetricos_500), MATCH_TARGETS["goals_per_match"], "goals/match")


def test_goals_home_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _goles_local(partidos_simetricos_500),
        MATCH_TARGETS["goals_home_per_match"],
        "goals_home/match",
    )


def test_goals_away_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _goles_visit(partidos_simetricos_500),
        MATCH_TARGETS["goals_away_per_match"],
        "goals_away/match",
    )


def test_home_win_pct(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    rs = partidos_simetricos_500
    pct = sum(1 for r in rs if r.estadisticas_local.goles > r.estadisticas_visitante.goles) / len(
        rs
    )
    assert_target(pct, MATCH_TARGETS["home_win_pct"], "home_win_pct")


def test_draw_pct(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    rs = partidos_simetricos_500
    pct = sum(1 for r in rs if r.estadisticas_local.goles == r.estadisticas_visitante.goles) / len(
        rs
    )
    assert_target(pct, MATCH_TARGETS["draw_pct"], "draw_pct")


def test_away_win_pct(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    rs = partidos_simetricos_500
    pct = sum(1 for r in rs if r.estadisticas_local.goles < r.estadisticas_visitante.goles) / len(
        rs
    )
    assert_target(pct, MATCH_TARGETS["away_win_pct"], "away_win_pct")


def test_shots_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(_tiros(partidos_simetricos_500), MATCH_TARGETS["shots_per_match"], "shots/match")


def test_shots_on_target_per_match(
    partidos_simetricos_500: list[ResultadoSimulacionPartido],
) -> None:
    assert_target(
        _sot(partidos_simetricos_500), MATCH_TARGETS["shots_on_target_per_match"], "SOT/match"
    )


def test_sot_ratio(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(_sot_ratio(partidos_simetricos_500), MATCH_TARGETS["sot_ratio"], "SOT_ratio")


def test_possession_home_pct(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _pos_local(partidos_simetricos_500),
        MATCH_TARGETS["possession_home_pct"],
        "possession_home_pct",
    )


def test_corners_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _corners(partidos_simetricos_500), MATCH_TARGETS["corners_per_match"], "corners/match"
    )


def test_fouls_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(_faltas(partidos_simetricos_500), MATCH_TARGETS["fouls_per_match"], "fouls/match")


def test_yellow_cards_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _amarillas(partidos_simetricos_500),
        MATCH_TARGETS["yellow_cards_per_match"],
        "yellows/match",
    )


def test_red_cards_per_match(partidos_simetricos_500: list[ResultadoSimulacionPartido]) -> None:
    assert_target(
        _rojas(partidos_simetricos_500), MATCH_TARGETS["red_cards_per_match"], "reds/match"
    )
