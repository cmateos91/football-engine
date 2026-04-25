# CALIBRATION_TARGETS.md

Valores objetivo de realismo para el motor de simulación de partidos de LaLiga.

Este archivo es la fuente de verdad para los tests estadísticos del proyecto.
Todos los valores proceden del archivo `docs/calibration/LaLiga_Stats_Calibracion_2024-25.xlsx`,
construido a partir de datos reales de la temporada 2024-25 y del histórico 2019-25.

**Regla de uso:** ningún parámetro del motor se ajusta a mano para pasar estos tests.
Si el motor no los supera, se abre una tarea de calibración documentada.

---

## Estructura del archivo

Este documento está diseñado para ser parseado automáticamente por los tests estadísticos.
Cada bloque `TARGETS` es un diccionario Python válido embebido en una sección de código.
El módulo `src/calibration/targets.py` lo importa y expone como constantes tipadas.

```
docs/
  calibration/
    CALIBRATION_TARGETS.md          ← este archivo (fuente humana + máquina)
    LaLiga_Stats_Calibracion_2024-25.xlsx  ← fuente de datos original
tests/
  statistical/
    conftest.py                     ← carga CALIBRATION_TARGETS en fixtures
    test_match_distributions.py
    test_season_distributions.py
    test_xg_model.py
    test_player_distributions.py
src/
  calibration/
    targets.py                      ← importa y expone las constantes
    scorecard.py                    ← genera informe automático vs targets
```

---

## 1. Métricas de partido — targets globales

Fuente: LaLiga 2024-25 (380 partidos) + histórico 2019-25 (6 temporadas).
Aplicable desde **Fase 3** (baseline). Severidades usadas en el scorecard automático.

```python
# src/calibration/targets.py  →  MATCH_TARGETS
MATCH_TARGETS = {

    # ── Goles ─────────────────────────────────────────────────────────────
    "goals_per_match": {
        "value": 2.62,
        "tolerance": 0.20,
        "range": (2.40, 2.85),
        "severity": "CRITICAL",
        "source": "Wikipedia 2024-25: 995 goles / 380 partidos",
        "historical_range": (2.46, 2.65),   # 6 temporadas 2019-25
    },
    "goals_home_per_match": {
        "value": 1.45,
        "tolerance": 0.15,
        "range": (1.30, 1.60),
        "severity": "CRITICAL",
        "source": "Estimación: ventaja local histórica LaLiga ~52 %",
    },
    "goals_away_per_match": {
        "value": 1.17,
        "tolerance": 0.15,
        "range": (1.05, 1.30),
        "severity": "CRITICAL",
        "source": "Calculado: 2.62 - 1.45",
    },

    # ── Resultados ────────────────────────────────────────────────────────
    "home_win_pct": {
        "value": 0.44,
        "tolerance": 0.04,
        "range": (0.40, 0.48),
        "severity": "CRITICAL",
        "source": "Histórico LaLiga 6 temporadas: 44-46 %",
        "historical_range": (0.44, 0.46),
    },
    "draw_pct": {
        "value": 0.25,
        "tolerance": 0.03,
        "range": (0.22, 0.28),
        "severity": "HIGH",
        "source": "Histórico LaLiga 6 temporadas: 24-26 %",
        "historical_range": (0.24, 0.26),
    },
    "away_win_pct": {
        "value": 0.31,
        "tolerance": 0.03,
        "range": (0.28, 0.34),
        "severity": "HIGH",
        "source": "Calculado: 1 - home_win_pct - draw_pct",
    },

    # ── Tiros ─────────────────────────────────────────────────────────────
    "shots_per_match": {
        "value": 23.0,
        "tolerance": 2.0,
        "range": (21.0, 26.0),
        "severity": "HIGH",
        "source": "Estimación Opta / FBref histórico LaLiga",
    },
    "shots_on_target_per_match": {
        "value": 8.0,
        "tolerance": 1.0,
        "range": (7.0, 9.5),
        "severity": "HIGH",
        "source": "Ratio SOT/tiros ~34 % LaLiga",
    },
    "sot_ratio": {
        "value": 0.34,
        "tolerance": 0.04,
        "range": (0.30, 0.38),
        "severity": "HIGH",
        "source": "Opta / FBref LaLiga",
    },

    # ── xG ────────────────────────────────────────────────────────────────
    "xg_per_match": {
        "value": 2.40,
        "tolerance": 0.25,
        "range": (2.10, 2.70),
        "severity": "HIGH",
        "source": "xG promedio LaLiga; siempre <= goles reales por varianza positiva",
        "note": "xG acumulado debe ser <= goles reales en simulación masiva",
    },
    "xg_per_shot": {
        "value": 0.104,
        "tolerance": 0.010,
        "range": (0.090, 0.120),
        "severity": "HIGH",
        "source": "Calculado: xg_per_match / shots_per_match",
    },

    # ── Posesión ─────────────────────────────────────────────────────────
    "possession_home_pct": {
        "value": 0.52,
        "tolerance": 0.04,
        "range": (0.48, 0.56),
        "severity": "MEDIUM",
        "source": "Ventaja ligera local; rango real por equipo 35-68 %",
    },

    # ── Eventos ──────────────────────────────────────────────────────────
    "corners_per_match": {
        "value": 10.0,
        "tolerance": 1.5,
        "range": (8.5, 11.5),
        "severity": "MEDIUM",
        "source": "Histórico LaLiga / TotalCorner",
    },
    "fouls_per_match": {
        "value": 22.0,
        "tolerance": 3.0,
        "range": (19.0, 26.0),
        "severity": "MEDIUM",
        "source": "FBref / Opta LaLiga",
    },
    "yellow_cards_per_match": {
        "value": 4.2,
        "tolerance": 0.5,
        "range": (3.5, 5.0),
        "severity": "MEDIUM",
        "source": "LaLiga: liga con más amarillas de Europa",
    },
    "red_cards_per_match": {
        "value": 0.12,
        "tolerance": 0.05,
        "range": (0.07, 0.18),
        "severity": "MEDIUM",
        "source": "~45-50 rojas por temporada en LaLiga",
    },
    "penalties_per_match": {
        "value": 0.24,
        "tolerance": 0.06,
        "range": (0.18, 0.30),
        "severity": "MEDIUM",
        "source": "~90 penaltis por temporada en LaLiga",
    },

    # ── Otros ─────────────────────────────────────────────────────────────
    "btts_pct": {
        "value": 0.53,
        "tolerance": 0.05,
        "range": (0.48, 0.58),
        "severity": "MEDIUM",
        "source": "BTTS LaLiga 2024-25",
    },
    "clean_sheet_rate": {
        "value": 0.52,
        "tolerance": 0.08,
        "range": (0.45, 0.60),
        "severity": "MEDIUM",
        "source": "~30 % de partidos con clean sheet para al menos un equipo",
        "note": "clean_sheet_rate es por equipo por partido, no por partido",
    },
    "header_goal_pct": {
        "value": 0.20,
        "tolerance": 0.04,
        "range": (0.16, 0.26),
        "severity": "MEDIUM",
        "source": "Histórico europeo: ~20-25 % goles de cabeza",
    },
    "own_goal_rate_per_season": {
        "value": 15,
        "tolerance": 5,
        "range": (10, 20),
        "severity": "LOW",
        "source": "Estimación histórica LaLiga",
    },
}
```

---

## 2. Distribución temporal de goles

Fuente: histórico LaLiga / Opta.
Aplicable desde **Fase 7** (motor de eventos avanzado).

```python
# src/calibration/targets.py  →  GOAL_TIMING_TARGETS
GOAL_TIMING_TARGETS = {
    # Fracciones del total de goles del partido por tramo de 15 minutos
    # Los valores suman 1.0 con tolerancia ± individual
    "0_15":  {"value": 0.09, "tolerance": 0.02, "severity": "MEDIUM"},
    "16_30": {"value": 0.14, "tolerance": 0.02, "severity": "MEDIUM"},
    "31_45": {"value": 0.13, "tolerance": 0.02, "severity": "MEDIUM"},
    "46_60": {"value": 0.15, "tolerance": 0.02, "severity": "MEDIUM"},
    "61_75": {"value": 0.17, "tolerance": 0.02, "severity": "MEDIUM"},
    "76_90": {"value": 0.21, "tolerance": 0.03, "severity": "MEDIUM"},
    "90+":   {"value": 0.11, "tolerance": 0.03, "severity": "LOW"},
}
```

---

## 3. Tipos de gol

Fuente: Opta / FBref / histórico LaLiga.
Aplicable desde **Fase 7**.

```python
# src/calibration/targets.py  →  GOAL_TYPE_TARGETS
GOAL_TYPE_TARGETS = {
    "open_play":    {"value": 0.55, "tolerance": 0.05, "severity": "HIGH"},
    "set_piece_fk": {"value": 0.07, "tolerance": 0.02, "severity": "MEDIUM"},
    "corner":       {"value": 0.10, "tolerance": 0.03, "severity": "MEDIUM"},
    "penalty":      {"value": 0.10, "tolerance": 0.02, "severity": "HIGH"},
    "counter":      {"value": 0.10, "tolerance": 0.03, "severity": "MEDIUM"},
    "cross":        {"value": 0.08, "tolerance": 0.03, "severity": "MEDIUM"},
    "own_goal":     {"value": 0.02, "tolerance": 0.01, "severity": "LOW"},
    # Invariante: sum de todas las fracciones debe ser 1.0 ± 0.02
}
```

---

## 4. Modelo xG — valores por zona de disparo

Fuente: Opta / StatsBomb / FBref (calibrado sobre LaLiga).
Aplicable desde **Fase 9** (modelo xG).

```python
# src/calibration/targets.py  →  XG_ZONE_TARGETS
XG_ZONE_TARGETS = {
    # zone_id: identificador interno de zona en EstadoEspacialPartido
    "six_yard_box": {
        "xg_mean": 0.55,
        "xg_range": (0.35, 0.75),
        "shot_pct": 0.05,
        "goal_pct": 0.20,
        "description": "Área pequeña, < 6m centro portería",
        "severity": "HIGH",
    },
    "penalty_spot_central": {
        "xg_mean": 0.28,
        "xg_range": (0.18, 0.40),
        "shot_pct": 0.10,
        "goal_pct": 0.22,
        "description": "6-11m, ángulo central",
        "severity": "HIGH",
    },
    "penalty_spot_lateral": {
        "xg_mean": 0.12,
        "xg_range": (0.07, 0.18),
        "shot_pct": 0.10,
        "goal_pct": 0.09,
        "description": "6-11m, ángulo lateral > 30°",
        "severity": "MEDIUM",
    },
    "box_central": {
        "xg_mean": 0.10,
        "xg_range": (0.06, 0.14),
        "shot_pct": 0.15,
        "goal_pct": 0.12,
        "description": "Frontal área, 12-18m, eje central",
        "severity": "HIGH",
    },
    "box_lateral": {
        "xg_mean": 0.07,
        "xg_range": (0.04, 0.10),
        "shot_pct": 0.10,
        "goal_pct": 0.05,
        "description": "Frontal área, 12-18m, ángulo lateral",
        "severity": "MEDIUM",
    },
    "outside_box_central": {
        "xg_mean": 0.05,
        "xg_range": (0.03, 0.08),
        "shot_pct": 0.18,
        "goal_pct": 0.07,
        "description": "Fuera área central, 19-25m",
        "severity": "MEDIUM",
    },
    "outside_box_lateral": {
        "xg_mean": 0.03,
        "xg_range": (0.01, 0.05),
        "shot_pct": 0.15,
        "goal_pct": 0.03,
        "description": "Fuera área lateral, 19-25m",
        "severity": "LOW",
    },
    "long_range": {
        "xg_mean": 0.02,
        "xg_range": (0.01, 0.04),
        "shot_pct": 0.17,
        "goal_pct": 0.02,
        "description": "> 25m, cualquier ángulo",
        "severity": "LOW",
    },
    "header_in_box": {
        "xg_mean": 0.09,
        "xg_range": (0.05, 0.14),
        "shot_pct": 0.15,
        "goal_pct": 0.10,
        "description": "Remate de cabeza desde zona de área",
        "severity": "HIGH",
    },
    "penalty": {
        "xg_mean": 0.76,
        "xg_range": (0.72, 0.80),
        "shot_pct": 0.03,
        "goal_pct": 0.10,
        "description": "Punto de penalti",
        "severity": "CRITICAL",
    },
}

# Modificadores multiplicativos del xG base
XG_MODIFIERS = {
    "strong_foot":        {"multiplier": 1.00, "range": (1.00, 1.00)},
    "weak_foot":          {"multiplier": 0.75, "range": (0.65, 0.85)},
    "high_pressure":      {"multiplier": 0.65, "range": (0.55, 0.75)},
    "no_pressure":        {"multiplier": 1.25, "range": (1.15, 1.35)},
    "quality_assist":     {"multiplier": 1.15, "range": (1.05, 1.25)},
    "counter_attack":     {"multiplier": 1.10, "range": (1.00, 1.20)},
    "header":             {"multiplier": 0.75, "range": (0.65, 0.85),
                           "note": "Adicional al xg base de zona; no aplica en six_yard_box"},
    "fatigue_high":       {"multiplier": 0.90, "range": (0.82, 0.95),
                           "note": "> 80 minutos jugados con carga acumulada"},
    "composure_elite":    {"multiplier": 1.08, "range": (1.04, 1.12),
                           "note": "Atributo compostura > 85"},
    "composure_low":      {"multiplier": 0.88, "range": (0.82, 0.94),
                           "note": "Atributo compostura < 55"},
}

# Invariante duro: xG resultante siempre en [0.001, 0.99]
XG_HARD_BOUNDS = (0.001, 0.99)
```

---

## 5. Métricas de temporada completa

Fuente: LaLiga 2024-25 + histórico 2019-25.
Aplicable desde **Fase 10** (simulación de temporada).

```python
# src/calibration/targets.py  →  SEASON_TARGETS
SEASON_TARGETS = {
    "champion_points": {
        "value": 88,
        "tolerance": 6,
        "range": (82, 95),
        "severity": "CRITICAL",
        "source": "LaLiga 2024-25: Barcelona 88 pts. Histórico 2019-25: 86-95",
        "historical_range": (86, 95),
    },
    "relegation_pts_18th": {
        "value": 40,
        "tolerance": 5,
        "range": (33, 46),
        "severity": "HIGH",
        "source": "LaLiga 2024-25: Leganés 40 pts (18º)",
    },
    "relegation_pts_20th": {
        "value": 16,
        "tolerance": 8,
        "range": (10, 26),
        "severity": "MEDIUM",
        "source": "LaLiga 2024-25: Valladolid 16 pts (20º, outlier histórico)",
        "note": "Rango amplio: el peor equipo tiene alta varianza",
    },
    "champion_goal_diff": {
        "value": 63,
        "tolerance": 15,
        "range": (40, 80),
        "severity": "MEDIUM",
        "source": "Barcelona 2024-25: +63. Rango histórico amplio",
    },
    "top_scorer_goals": {
        "value": 25,
        "tolerance": 8,
        "range": (18, 35),
        "severity": "MEDIUM",
        "source": "Histórico 2019-25: 19-31 goles. Media ~24",
        "note": "Alta varianza individual; el motor debe reproducir la distribución, no el valor exacto",
    },
    "total_league_goals": {
        "value": 995,
        "tolerance": 80,
        "range": (900, 1080),
        "severity": "CRITICAL",
        "source": "LaLiga 2024-25: 995 goles en 380 partidos",
    },
    "teams_over_60_pts": {
        "value": 3,
        "tolerance": 2,
        "range": (1, 6),
        "severity": "MEDIUM",
        "source": "LaLiga 2024-25: Barcelona(88), Madrid(84), Atlético(76)",
    },
    "teams_under_35_pts": {
        "value": 1,
        "tolerance": 1,
        "range": (0, 3),
        "severity": "MEDIUM",
        "source": "Normalmente 1-2 equipos muy débiles por temporada",
    },
}
```

---

## 6. Distribución histórica multi-temporada

Para validación cruzada temporal (Fase 12).
El motor calibrado sobre 2019-22 debe validarse sobre 2022-25.

```python
# src/calibration/targets.py  →  HISTORICAL_SEASONS
HISTORICAL_SEASONS = [
    {"season": "2024-25", "champion": "FC Barcelona",    "champion_pts": 88, "goals_per_match": 2.62, "home_win_pct": 0.44, "draw_pct": 0.25, "top_scorer_goals": 31},
    {"season": "2023-24", "champion": "Real Madrid",     "champion_pts": 95, "goals_per_match": 2.65, "home_win_pct": 0.45, "draw_pct": 0.24, "top_scorer_goals": 23},
    {"season": "2022-23", "champion": "FC Barcelona",    "champion_pts": 88, "goals_per_match": 2.65, "home_win_pct": 0.46, "draw_pct": 0.24, "top_scorer_goals": 19},
    {"season": "2021-22", "champion": "Real Madrid",     "champion_pts": 86, "goals_per_match": 2.54, "home_win_pct": 0.44, "draw_pct": 0.25, "top_scorer_goals": 27},
    {"season": "2020-21", "champion": "Atlético Madrid", "champion_pts": 86, "goals_per_match": 2.46, "home_win_pct": 0.44, "draw_pct": 0.26, "top_scorer_goals": 30},
    {"season": "2019-20", "champion": "Real Madrid",     "champion_pts": 87, "goals_per_match": 2.64, "home_win_pct": 0.44, "draw_pct": 0.25, "top_scorer_goals": 25},
]

# Rangos derivados de las 6 temporadas (usados como ventana de calibración temporal)
HISTORICAL_RANGES = {
    "goals_per_match":  {"min": 2.46, "max": 2.65, "mean": 2.59},
    "champion_pts":     {"min": 86,   "max": 95,   "mean": 88.3},
    "home_win_pct":     {"min": 0.44, "max": 0.46, "mean": 0.445},
    "draw_pct":         {"min": 0.24, "max": 0.26, "mean": 0.248},
    "top_scorer_goals": {"min": 19,   "max": 31,   "mean": 24.2},
}
```

---

## 7. Invariantes duros del motor

Estos deben pasar **siempre**, en cualquier simulación, con cualquier seed o configuración.
Se verifican en `tests/unit/test_invariants.py` y en `tests/statistical/test_invariants_mass.py`.

```python
# src/calibration/targets.py  →  HARD_INVARIANTS
HARD_INVARIANTS = [
    # Partido
    {"id": "INV-001", "description": "Goles >= 0 para cualquier equipo",             "severity": "CRITICAL"},
    {"id": "INV-002", "description": "Tiros a puerta <= tiros totales",               "severity": "CRITICAL"},
    {"id": "INV-003", "description": "xG ∈ [0.001, 0.99] para cualquier disparo",    "severity": "CRITICAL"},
    {"id": "INV-004", "description": "Minutos de partido ∈ [90, 100]",               "severity": "CRITICAL"},
    {"id": "INV-005", "description": "Posesión local + posesión visitante = 100 %",  "severity": "CRITICAL"},
    {"id": "INV-006", "description": "Resultado es consistente con log de goles",    "severity": "CRITICAL"},
    {"id": "INV-007", "description": "Seed fija produce resultado idéntico",         "severity": "CRITICAL"},
    # Temporada
    {"id": "INV-008", "description": "Cada equipo juega exactamente 38 partidos",   "severity": "CRITICAL"},
    {"id": "INV-009", "description": "Cada equipo: 19 local + 19 visitante",        "severity": "CRITICAL"},
    {"id": "INV-010", "description": "Suma de puntos = partidos × 3 si no hay empate, o coherente", "severity": "CRITICAL"},
    {"id": "INV-011", "description": "Puntos ∈ [0, 114] para cualquier equipo",     "severity": "CRITICAL"},
    # xG
    {"id": "INV-012", "description": "xG acumulado liga <= goles reales acumulados en run largo", "severity": "HIGH",
     "note": "En un run corto puede invertirse por varianza; en 1000+ partidos debe cumplirse"},
    # Parámetros calibrados
    {"id": "INV-013", "description": "Todo parámetro calibrado está dentro de su rango válido declarado", "severity": "CRITICAL"},
]
```

---

## 8. Guía de uso en tests

### Cargar targets en pytest

```python
# tests/statistical/conftest.py
import pytest
from src.calibration.targets import (
    MATCH_TARGETS,
    SEASON_TARGETS,
    XG_ZONE_TARGETS,
    XG_MODIFIERS,
    GOAL_TIMING_TARGETS,
    GOAL_TYPE_TARGETS,
    HARD_INVARIANTS,
    HISTORICAL_SEASONS,
)

@pytest.fixture(scope="session")
def match_targets():
    return MATCH_TARGETS

@pytest.fixture(scope="session")
def season_targets():
    return SEASON_TARGETS

@pytest.fixture(scope="session")
def xg_targets():
    return XG_ZONE_TARGETS, XG_MODIFIERS
```

### Ejemplo de test estadístico

```python
# tests/statistical/test_match_distributions.py
def test_goals_per_match(simulated_matches, match_targets):
    """Valida que goals/partido cae dentro de la tolerancia LaLiga."""
    target = match_targets["goals_per_match"]
    mean_goals = sum(m.total_goals for m in simulated_matches) / len(simulated_matches)
    delta = abs(mean_goals - target["value"])
    assert delta <= target["tolerance"], (
        f"goals/match = {mean_goals:.3f}, target = {target['value']} ± {target['tolerance']}. "
        f"Delta = {delta:.3f}. Severidad: {target['severity']}"
    )
```

### Ejemplo de test de sensibilidad

```python
# tests/statistical/test_sensitivity.py
def test_finishing_attribute_monotonicity(simulate_match):
    """Subir finishing debe aumentar xG medio del equipo."""
    base  = simulate_match(finishing=60, n=500)
    high  = simulate_match(finishing=85, n=500)
    assert high.mean_xg > base.mean_xg, "finishing alto debe producir mayor xG"
```

---

## 9. Ciclo de vida del archivo

| Evento | Acción |
|---|---|
| Nueva temporada de LaLiga disponible | Actualizar valores en el `.xlsx` y regenerar este `.md` |
| El motor no pasa un target CRÍTICO | Abrir tarea de calibración; no avanzar de milestone |
| El motor no pasa un target ALTO | Documentar en el informe de versión; justificar o corregir |
| Se activa un nuevo grupo de atributos (Fase 5) | Añadir tests de sensibilidad para ese grupo; no modificar targets globales |
| Fase 12: calibración automática | Los parámetros optimizados se validan contra este archivo antes de congelar |
| Discrepancia entre `.xlsx` y este `.md` | Este `.md` es la fuente autoritativa para el código; el `.xlsx` es la fuente de datos original |

---

## 10. Fuentes y versioning

| Fuente | Cobertura | URL de referencia |
|---|---|---|
| Wikipedia 2024-25 La Liga | Clasificación final, goles, partidos | en.wikipedia.org/wiki/2024–25_La_Liga |
| NBC Sports / SI.com | Goleadores, estadísticas de equipo | nbcsports.com / si.com |
| Opta / FBref | Tiros, SOT, xG, posesión | fbref.com/comps/12 |
| Sofascore | Promedio goles 2024-25 | sofascore.com |
| TotalCorner | Córners, tarjetas | totalcorner.com |

**Versión del archivo:** 1.0.0
**Temporada de referencia principal:** 2024-25
**Temporadas históricas incluidas:** 2019-20 → 2024-25
**Última actualización:** Abril 2026
**Próxima revisión:** Al finalizar LaLiga 2025-26 (mayo 2026)
