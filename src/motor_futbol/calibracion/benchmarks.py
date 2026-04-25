"""Benchmarks de LaLiga para validación estadística del motor."""

from __future__ import annotations

from typing import Any

from motor_futbol.calibracion.targets import MATCH_TARGETS

BENCHMARKS_LALIGA = {
    "goles_por_partido": {"min": 1.5, "max": 3.5, "ideal": 2.4},
    "tiros_por_partido": {"min": 9.0, "max": 17.0, "ideal": 13.0},
    "tiros_a_puerta_por_partido": {"min": 3.0, "max": 7.5, "ideal": 5.0},
    "posesion_local": {"min": 48.0, "max": 60.0, "ideal": 53.0},
    "posesion_visitante": {"min": 40.0, "max": 52.0, "ideal": 47.0},
    "corners_por_partido": {"min": 0.5, "max": 5.0, "ideal": 2.5},
    "faltas_por_partido": {"min": 8.0, "max": 20.0, "ideal": 14.0},
    "tarjetas_amarillas_por_partido": {"min": 1.5, "max": 5.5, "ideal": 3.5},
    "tarjetas_rojas_por_partido": {"min": 0.03, "max": 0.40, "ideal": 0.18},
    "victoria_local_pct": {"min": 0.35, "max": 0.60, "ideal": 0.47},
    "empate_pct": {"min": 0.15, "max": 0.45, "ideal": 0.30},
    "victoria_visitante_pct": {"min": 0.15, "max": 0.40, "ideal": 0.26},
}


BENCHMARKS_EQUIPO = {
    "goles_por_equipo_por_partido": {"min": 0.9, "max": 1.9, "ideal": 1.3},
    "tiros_por_equipo_por_partido": {"min": 5.0, "max": 8.0, "ideal": 6.5},
    "tiros_a_puerta_por_equipo_por_partido": {"min": 1.8, "max": 3.5, "ideal": 2.5},
    "posesion_por_equipo_por_partido": {"min": 44.0, "max": 56.0, "ideal": 50.0},
}


class RealismScorecard:
    """Evalúa la calidad de una simulación masiva contra targets reales."""

    def __init__(self, resultados: list[Any]):
        self.resultados = resultados
        self.metricas: dict[str, float] = {}
        self._calcular_metricas()

    def _calcular_metricas(self) -> None:
        if not self.resultados:
            return

        n = len(self.resultados)
        self.metricas["goals_per_match"] = sum(r.total_goles for r in self.resultados) / n
        self.metricas["shots_per_match"] = sum(r.total_tiros for r in self.resultados) / n
        self.metricas["shots_on_target_per_match"] = (
            sum(
                r.estadisticas_local.tiros_a_puerta + r.estadisticas_visitante.tiros_a_puerta
                for r in self.resultados
            )
            / n
        )
        self.metricas["possession_home_pct"] = sum(
            r.estadisticas_local.posesion_pct for r in self.resultados
        ) / (n * 100.0)

    def evaluar(self) -> dict[str, Any]:
        informe: dict[str, Any] = {"score_global": 0.0, "detalles": {}, "pasado": True}
        puntos_totales = 0
        puntos_obtenidos = 0

        pesos = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}

        for metrica, target in MATCH_TARGETS.items():
            if metrica not in self.metricas:
                continue

            valor = self.metricas[metrica]
            diff = abs(valor - target["value"])
            tolerancia = target["tolerance"]
            peso = pesos.get(target["severity"], 1)
            puntos_totales += peso

            cumple = diff <= tolerancia
            if cumple:
                puntos_obtenidos += peso
            else:
                if target["severity"] == "CRITICAL":
                    informe["pasado"] = False

            informe["detalles"][metrica] = {
                "valor": round(valor, 3),
                "objetivo": target["value"],
                "delta": round(diff, 3),
                "cumple": cumple,
                "severidad": target["severity"],
            }

        if puntos_totales > 0:
            informe["score_global"] = (puntos_obtenidos / puntos_totales) * 100.0

        return informe


def esta_en_rango(valor: float, benchmark: dict[str, float]) -> bool:
    return benchmark["min"] <= valor <= benchmark["max"]


def verificar_benchmark(valor: float, benchmark: dict[str, float]) -> tuple[bool, str]:
    if valor < benchmark["min"]:
        return False, f"Valor {valor:.2f} está por debajo del mínimo {benchmark['min']}"
    if valor > benchmark["max"]:
        return False, f"Valor {valor:.2f} está por encima del máximo {benchmark['max']}"
    return True, f"Valor {valor:.2f} está en rango [{benchmark['min']}, {benchmark['max']}]"
