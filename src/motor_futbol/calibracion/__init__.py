"""Calibración del motor de simulación."""

from motor_futbol.calibracion.benchmarks import (
    BENCHMARKS_EQUIPO,
    BENCHMARKS_LALIGA,
    esta_en_rango,
    verificar_benchmark,
)
from motor_futbol.calibracion.targets import (
    GOAL_TIMING_TARGETS,
    GOAL_TYPE_TARGETS,
    HARD_INVARIANTS,
    HISTORICAL_RANGES,
    HISTORICAL_SEASONS,
    MATCH_TARGETS,
    SEASON_TARGETS,
    XG_HARD_BOUNDS,
    XG_MODIFIERS,
    XG_ZONE_TARGETS,
)

__all__ = [
    # Benchmarks legacy (rangos permisivos, conservar compatibilidad)
    "BENCHMARKS_EQUIPO",
    "BENCHMARKS_LALIGA",
    "GOAL_TIMING_TARGETS",
    "GOAL_TYPE_TARGETS",
    "HARD_INVARIANTS",
    "HISTORICAL_RANGES",
    "HISTORICAL_SEASONS",
    # Targets autoritativos (fuente: CALIBRATION_TARGETS.md)
    "MATCH_TARGETS",
    "SEASON_TARGETS",
    "XG_HARD_BOUNDS",
    "XG_MODIFIERS",
    "XG_ZONE_TARGETS",
    "esta_en_rango",
    "verificar_benchmark",
]
