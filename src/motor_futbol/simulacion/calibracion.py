"""Calibración automatizada del motor."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Any

from motor_futbol.dominio import Equipo
from motor_futbol.simulacion.modelos import ParametrosSimulacionBaseline
from motor_futbol.simulacion.motor_baseline import simular_partido_baseline
from motor_futbol.simulacion.temporada import crear_equipos_default


@dataclass
class MetasLaLiga:
    """Metas de LaLiga para calibración."""

    goles_por_partido: float = 2.52
    tiros_por_partido: float = 13.5
    posesion_local_pct: float = 50.3
    corners_por_partido: float = 5.5
    tarjetas_amarillas_pct: float = 35.0
    conversion_tiros_pct: float = 18.5
    xg_media: float = 0.11


@dataclass
class ResultadoCalibracion:
    """Resultado de una carrera de calibración."""

    parametros: ParametrosSimulacionBaseline
    score: float
    errores: dict[str, float]
    iteraciones: int
    convergencia: list[float] = field(default_factory=list)

    def a_dict(self) -> dict[str, Any]:
        return {
            "parametros": {
                "posesiones_base": self.parametros.posesiones_base,
                "posesiones_variacion": self.parametros.variacion_posesiones,
                "probabilidad_base_tiro": self.parametros.probabilidad_base_tiro,
                "probabilidad_base_falta": self.parametros.probabilidad_base_falta,
                "probabilidad_base_corner": self.parametros.probabilidad_base_corner,
                "probabilidad_base_tiro_puerta": self.parametros.probabilidad_base_tiro_puerta,
                "probabilidad_base_gol": self.parametros.probabilidad_base_gol,
            },
            "score": round(self.score, 4),
            "errores": {k: round(v, 4) for k, v in self.errores.items()},
            "iteraciones": self.iteraciones,
        }


def _simular_y_medir(
    parametros: ParametrosSimulacionBaseline,
    equipos: list[Equipo],
    n_partidos: int,
    semilla_base: int,
) -> dict[str, float]:
    """Simula partidos y retorna métricas."""
    Random(semilla_base)

    totales: dict[str, float] = {
        "goles": 0.0,
        "tiros": 0.0,
        "posesion_local": 0.0,
        "corners": 0.0,
        "tarjetas_amarillas": 0.0,
    }
    partidos_validos = 0

    for i in range(n_partidos):
        eq_local = equipos[i % len(equipos)]
        eq_visita = equipos[(i + 1) % len(equipos)]

        from motor_futbol.dominio import ContextoPartido

        contexto = ContextoPartido(
            competicion="Calibracion",
            temporada="2025",
            equipo_local=eq_local,
            equipo_visitante=eq_visita,
            semilla=semilla_base + i,
        )

        try:
            resultado = simular_partido_baseline(contexto, parametros=parametros)

            totales["goles"] += resultado.total_goles
            totales["tiros"] += resultado.total_tiros
            totales["posesion_local"] += resultado.estadisticas_local.posesion_pct
            totales["corners"] += resultado.estadisticas_local.corners
            totales["tarjetas_amarillas"] += resultado.estadisticas_local.tarjetas_amarillas
            partidos_validos += 1
        except Exception:
            pass

    if partidos_validos == 0:
        return {}

    return {
        "goles_por_partido": totales["goles"] / partidos_validos,
        "tiros_por_partido": totales["tiros"] / partidos_validos,
        "posesion_local_pct": totales["posesion_local"] / partidos_validos,
        "corners_por_partido": totales["corners"] / partidos_validos,
        "tarjetas_pct": (totales["tarjetas_amarillas"] / partidos_validos) * 100,
    }


def _calcular_error(
    metricas: dict[str, float],
    metas: MetasLaLiga,
) -> tuple[float, dict[str, float]]:
    """Calcula error total vs metas."""
    errores = {}

    if "goles_por_partido" in metricas:
        errores["goles"] = abs(metricas["goles_por_partido"] - metas.goles_por_partido)

    if "tiros_por_partido" in metricas:
        errores["tiros"] = (
            abs(metricas["tiros_por_partido"] - metas.tiros_por_partido) / metas.tiros_por_partido
        )

    if "shots_on_target_per_match" in metricas:
        errores["sot"] = abs(metricas["shots_on_target_per_match"] - 8.0) / 8.0

    if "posesion_local_pct" in metricas:
        errores["posesion"] = abs(metricas["posesion_local_pct"] - metas.posesion_local_pct) / 100.0

    if "corners_por_partido" in metricas:
        errores["corners"] = (
            abs(metricas["corners_por_partido"] - metas.corners_por_partido)
            / metas.corners_por_partido
        )

    error_total = sum(errores.values()) / max(1, len(errores))

    return error_total, errores


def calibrar_parametros(
    *,
    metas: MetasLaLiga | None = None,
    n_partidos: int = 50,
    max_iteraciones: int = 40,
    semilla: int = 20250601,
) -> ResultadoCalibracion:
    """Busca parámetros óptimos usando scipy.optimize."""
    import numpy as np
    from scipy.optimize import minimize  # type: ignore[import-untyped]

    metas = metas or MetasLaLiga()
    equipos = crear_equipos_default()
    convergencia = []

    # Vector inicial de parámetros normalizados [0, 1]
    # 0: posesiones_base (100-180)
    # 1: variacion_posesiones (10-40)
    # 2: probabilidad_base_tiro (0.10-0.30)
    # 3: probabilidad_base_falta (0.05-0.20)
    # 4: probabilidad_base_corner = 0.20 fixed approx
    # 5: probabilidad_base_tiro_puerta (0.25-0.50)
    # 6: probabilidad_base_gol (0.15-0.40) -> Subimos rango para recuperar goles
    x0 = np.array([0.4, 0.3, 0.45, 0.4, 0.3, 0.5, 0.5])

    def _objetivo(x: Any) -> float:
        # Desnormalizar
        p_base = int(100 + x[0] * 80)
        p_var = int(10 + x[1] * 30)
        p_tiro = 0.10 + x[2] * 0.20
        p_falta = 0.05 + x[3] * 0.15
        p_corner = 0.15 + x[4] * 0.20
        p_sot = 0.25 + x[5] * 0.25
        p_gol = 0.15 + x[6] * 0.25

        params = ParametrosSimulacionBaseline(
            posesiones_base=p_base,
            variacion_posesiones=p_var,
            probabilidad_base_tiro=p_tiro,
            probabilidad_base_falta=p_falta,
            probabilidad_base_corner=p_corner,
            probabilidad_base_tiro_puerta=p_sot,
            probabilidad_base_gol=p_gol,
        )

        metricas = _simular_y_medir(params, equipos, n_partidos, semilla)
        if not metricas:
            return 1.0

        score, errores = _calcular_error(metricas, metas)

        # Ponderación equilibrada para todas las métricas críticas
        # SOT/match objetivo es 8.0. Goles 2.62. Tiros 23.0
        # Calculamos el error relativo del SOT también
        error_sot = (
            abs(metricas.get("shots_on_target_per_match", 0) - metas.xg_media * 72) / 8.0
        )  # fallback aproximado
        if "shots_on_target_per_match" in metricas:
            error_sot = abs(metricas["shots_on_target_per_match"] - 8.0) / 8.0

        error_ponderado = (
            errores.get("goles", 0) * 2.0
            + errores.get("tiros", 0) * 1.5
            + error_sot * 2.0
            + errores.get("posesion", 0) * 0.5
        ) / 6.0

        convergencia.append(error_ponderado)
        return error_ponderado

    res = minimize(
        _objetivo,
        x0,
        method="Nelder-Mead",
        options={"maxiter": max_iteraciones, "xatol": 0.01},
        bounds=[(0, 1)] * 7,
        callback=lambda x: print(".", end="", flush=True),
    )
    print()  # Nueva línea tras los puntos de progreso

    # Reconstruir mejores parámetros
    x_opt = res.x
    mejor_params = ParametrosSimulacionBaseline(
        posesiones_base=int(100 + x_opt[0] * 80),
        variacion_posesiones=int(10 + x_opt[1] * 30),
        probabilidad_base_tiro=0.10 + x_opt[2] * 0.20,
        probabilidad_base_falta=0.05 + x_opt[3] * 0.15,
        probabilidad_base_corner=0.15 + x_opt[4] * 0.20,
        probabilidad_base_tiro_puerta=0.25 + x_opt[5] * 0.25,
        probabilidad_base_gol=0.15 + x_opt[6] * 0.25,
    )

    metricas_final = _simular_y_medir(mejor_params, equipos, n_partidos, semilla)
    _, errores = (
        _calcular_error(metricas_final, metas) if metricas_final else (0.0, {})
    )

    return ResultadoCalibracion(
        parametros=mejor_params,
        score=float(res.fun),
        errores=errores,
        iteraciones=int(res.nit),
        convergencia=convergencia,
    )


def validar_parametros(
    params: ParametrosSimulacionBaseline,
    *,
    n_partidos: int = 100,
    semilla: int = 999999,
) -> dict[str, Any]:
    """Valida que los parámetros cumplen invariantes."""
    equipos = crear_equipos_default()

    metricas = _simular_y_medir(params, equipos, n_partidos, semilla)

    errores_invariantes = {}

    if metricas.get("goles_por_partido", 0) < 1.5:
        errores_invariantes["goles_bajos"] = "Menos de 1.5 goles/partido"

    if metricas.get("goles_por_partido", 0) > 4.5:
        errores_invariantes["goles_altos"] = "Más de 4.5 goles/partido"

    if metricas.get("tiros_por_partido", 0) < 8:
        errores_invariantes["pocos_tiros"] = "Menos de 8 tiros/partido"

    posesion = metricas.get("posesion_local_pct", 50)
    if posesion < 40 or posesion > 65:
        errores_invariantes["posesion_extrema"] = f"Posesión local {posesion}% fuera de rango"

    return {
        "valido": len(errores_invariantes) == 0,
        "errores": errores_invariantes,
        "metricas": metricas,
    }


class RegistroCalibracion:
    """Registro de experimentos de calibración."""

    def __init__(self) -> None:
        self.experimentos: list[dict[str, Any]] = []

    def agregar(self, resultado: ResultadoCalibracion, metadata: dict[str, Any]) -> None:
        self.experimentos.append(
            {
                **resultado.a_dict(),
                **metadata,
            }
        )

    def mejor_experimento(self) -> dict[str, Any] | None:
        if not self.experimentos:
            return None

        return min(self.experimentos, key=lambda x: x["score"])

    def top(self, n: int = 5) -> list[dict[str, Any]]:
        ordenados = sorted(self.experimentos, key=lambda x: x["score"])
        return ordenados[:n]

    def a_dict(self) -> dict[str, Any]:
        return {"experimentos": self.experimentos}
