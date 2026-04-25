"""Fixtures y helpers compartidos para tests estadísticos."""

from __future__ import annotations

import random

import pytest

from motor_futbol.simulacion import simular_partido_baseline
from motor_futbol.simulacion.modelos import ResultadoSimulacionPartido


def assert_target(valor: float, target: dict, nombre: str) -> None:
    """Verifica que valor esté dentro de value ± tolerance del target."""
    delta = abs(valor - target["value"])
    assert delta <= target["tolerance"], (
        f"{nombre} = {valor:.4f} | objetivo = {target['value']} ± {target['tolerance']} "
        f"| delta = {delta:.4f} | severidad = {target['severity']}"
    )


@pytest.fixture(scope="session")
def partidos_simetricos_500() -> list[ResultadoSimulacionPartido]:
    """500 partidos con equipos simétricos de nivel 75 — muestra de referencia."""
    from tests.unit.fabrica_dominio import (
        crear_contexto_baseline_desde_equipos,
        crear_equipo_con_nivel,
    )

    eq_a = crear_equipo_con_nivel(id_equipo=1, nombre="Local", nivel_general=75)
    eq_b = crear_equipo_con_nivel(id_equipo=2, nombre="Visitante", nivel_general=75)
    random.seed(1000)
    seeds = [random.randint(1, 100_000) for _ in range(500)]
    return [
        simular_partido_baseline(crear_contexto_baseline_desde_equipos(eq_a, eq_b, semilla=s))
        for s in seeds
    ]
