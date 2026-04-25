"""Modelo de Expected Goals (xG) basado en contexto."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees, sqrt
from typing import TYPE_CHECKING

from motor_futbol.dominio import Jugador, ZonaCampo

if TYPE_CHECKING:
    from motor_futbol.dominio import Alineacion


@dataclass(frozen=True)
class ContextoTiro:
    """Contexto completo de un tiro para calcular xG."""

    distancia: float
    angulo: float
    zona: ZonaCampo
    es_cabeza: bool
    es_contraataque: bool
    es_balon_parado: bool
    usa_pie_dominante: bool
    energia_tirador: float
    presion_defensiva: float
    calidad_tirador: float


@dataclass(frozen=True)
class ResultadoXG:
    """Resultado del cálculo de xG."""

    xg: float
    factores: dict[str, float | str]
    descripcion: str


POSICION_ARCO = (100.0, 50.0)

_XG_ZONE_BASE = {
    "six_yard_box": 0.55,
    "penalty_spot_central": 0.28,
    "penalty_spot_lateral": 0.12,
    "box_central": 0.10,
    "box_lateral": 0.07,
    "outside_box_central": 0.05,
    "outside_box_lateral": 0.03,
    "long_range": 0.02,
    "header_in_box": 0.09,
    "penalty": 0.76,
}

_XG_MODIFIERS = {
    "strong_foot": 1.00,
    "weak_foot": 0.75,
    "high_pressure": 0.65,
    "no_pressure": 1.25,
    "quality_assist": 1.15,
    "counter_attack": 1.10,
    "header": 0.75,
    "fatigue_high": 0.90,
    "composure_elite": 1.08,
    "composure_low": 0.88,
}

_XG_HARD_BOUNDS = (0.001, 0.99)


def _identificar_zona_semantica(
    distancia: float, angulo: float, es_cabeza: bool, es_penalti: bool
) -> str:
    """Identifica la zona semántica según distancia, ángulo y tipo."""
    if es_penalti:
        return "penalty"
    if distancia <= 12.0 and angulo <= 15:
        return "penalty"
    if es_cabeza and distancia <= 18.0:
        return "header_in_box"
    if distancia <= 5.5:
        return "six_yard_box"
    if distancia <= 11.0:
        if angulo <= 30:
            return "penalty_spot_central"
        return "penalty_spot_lateral"
    if distancia <= 18.0:
        if angulo <= 30:
            return "box_central"
        return "box_lateral"
    if distancia <= 25.0:
        if angulo <= 30:
            return "outside_box_central"
        return "outside_box_lateral"
    return "long_range"


def calcular_xg(
    tirador: Jugador,
    posicion_tiro: tuple[float, float],
    *,
    es_cabeza: bool = False,
    es_contraataque: bool = False,
    es_balon_parado: bool = False,
    usa_pie_dominante: bool = True,
    energia: float = 100.0,
    defensa: float = 50.0,
    alineacion_def: Alineacion | None = None,
) -> ResultadoXG:
    """Calcula xG para un tiro dado el contexto."""
    distancia = _calcular_distancia(posicion_tiro)
    angulo = _calcular_angulo(posicion_tiro)
    ZonaCampo.desde_xy(posicion_tiro[0], posicion_tiro[1])

    zona_id = _identificar_zona_semantica(distancia, angulo, es_cabeza, es_penalti=False)

    xg_base = _XG_ZONE_BASE.get(zona_id, 0.10)

    modifiers_product = 1.0

    if usa_pie_dominante:
        modifiers_product *= _XG_MODIFIERS["strong_foot"]
    else:
        modifiers_product *= _XG_MODIFIERS["weak_foot"]

    if distancia > 15.0 and es_cabeza:
        modifiers_product *= _XG_MODIFIERS["header"]

    if es_contraataque:
        modifiers_product *= _XG_MODIFIERS["counter_attack"]

    if es_balon_parado and not es_cabeza:
        modifiers_product *= _XG_MODIFIERS.get("quality_assist", 1.0)

    pressure_mod = 1.0
    if defensa >= 70:
        pressure_mod = _XG_MODIFIERS["high_pressure"]
    elif defensa < 40:
        pressure_mod = _XG_MODIFIERS["no_pressure"]
    modifiers_product *= pressure_mod

    if energia < 50:
        modifiers_product *= _XG_MODIFIERS["fatigue_high"]

    calidad = _factor_calidad_jugador(tirador)
    if calidad >= 85:
        modifiers_product *= _XG_MODIFIERS["composure_elite"]
    elif calidad <= 55:
        modifiers_product *= _XG_MODIFIERS["composure_low"]

    xg = xg_base * modifiers_product

    xg = max(_XG_HARD_BOUNDS[0], min(_XG_HARD_BOUNDS[1], xg))

    factores: dict[str, float | str] = {
        "zona": zona_id,
        "xg_base": xg_base,
        "modifiers_product": modifiers_product,
        "pie": _XG_MODIFIERS["strong_foot"] if usa_pie_dominante else _XG_MODIFIERS["weak_foot"],
        "presion": pressure_mod,
        "energia": _XG_MODIFIERS["fatigue_high"] if energia < 50 else 1.0,
        "cabeza": _XG_MODIFIERS["header"] if es_cabeza and distancia > 15.0 else 1.0,
        "contraataque": _XG_MODIFIERS["counter_attack"] if es_contraataque else 1.0,
        "calidad": calidad,
    }

    descripcion = f"xG={xg:.3f} ({zona_id}) base={xg_base:.2f}*mod={modifiers_product:.2f}"

    return ResultadoXG(xg=xg, factores=factores, descripcion=descripcion)


def _calcular_distancia(pos: tuple[float, float]) -> float:
    x, y = pos
    dx = POSICION_ARCO[0] - x
    dy = POSICION_ARCO[1] - y
    return sqrt(dx * dx + dy * dy)


def _calcular_angulo(pos: tuple[float, float]) -> float:
    x, y = pos
    dx = POSICION_ARCO[0] - x
    dy = POSICION_ARCO[1] - y
    angulo = atan2(abs(dy), dx)
    return degrees(angulo)


def _factor_calidad_jugador(jugador: Jugador) -> float:
    return (
        jugador.atributos.finalizacion * 0.40
        + jugador.atributos.potencia_tiro * 0.25
        + jugador.atributos.awareness_ofensivo * 0.20
        + jugador.atributos.regate * 0.15
    )
