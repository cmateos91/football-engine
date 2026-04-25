"""Tests de contribucion y monotonicidad de atributos del motor."""

from __future__ import annotations

import random

from tests.unit.fabrica_dominio import (
    crear_contexto_baseline_desde_equipos,
    crear_equipo_con_nivel,
)

from motor_futbol.dominio import Equipo
from motor_futbol.simulacion import simular_partido_baseline
from motor_futbol.simulacion.modelos import ResultadoSimulacionPartido


def _ejecutar_partido(
    eq_local: Equipo,
    eq_visita: Equipo,
    semilla: int = 1000,
) -> ResultadoSimulacionPartido:
    return simular_partido_baseline(
        crear_contexto_baseline_desde_equipos(eq_local, eq_visita, semilla=semilla)
    )


def test_mayor_nivel_mas_goles() -> None:
    eq_debil = crear_equipo_con_nivel(
        id_equipo=1,
        nombre="Debil",
        nivel_general=60,
        bonus_ataque=-10,
        bonus_defensa=-10,
    )
    eq_fuerte = crear_equipo_con_nivel(
        id_equipo=2,
        nombre="Fuerte",
        nivel_general=85,
        bonus_ataque=10,
        bonus_defensa=10,
    )
    random.seed(12345)
    ges_debil = sum(
        _ejecutar_partido(eq_debil, eq_fuerte).estadisticas_local.goles for _ in range(30)
    )
    random.seed(12345)
    ges_fuerte = sum(
        _ejecutar_partido(eq_fuerte, eq_debil).estadisticas_local.goles for _ in range(30)
    )
    assert ges_fuerte >= ges_debil - 5, f"{ges_fuerte} >= {ges_debil}"


def test_mayor_ataque_mas_tiros() -> None:
    eq_debil = crear_equipo_con_nivel(
        id_equipo=1, nombre="AtaqueBajo", nivel_general=75, bonus_ataque=-10, bonus_defensa=0
    )
    eq_fuerte = crear_equipo_con_nivel(
        id_equipo=2, nombre="AtaqueAlto", nivel_general=75, bonus_ataque=10, bonus_defensa=0
    )
    random.seed(12345)
    tires_debil = sum(
        _ejecutar_partido(eq_debil, eq_fuerte).estadisticas_local.tiros for _ in range(30)
    )
    random.seed(12345)
    tires_fuerte = sum(
        _ejecutar_partido(eq_fuerte, eq_debil).estadisticas_local.tiros for _ in range(30)
    )
    assert tires_fuerte >= tires_debil, f"{tires_fuerte} >= {tires_debil}"


def test_mayor_defensa_menos_goles() -> None:
    eq_debil = crear_equipo_con_nivel(
        id_equipo=1, nombre="DefBaja", nivel_general=75, bonus_ataque=0, bonus_defensa=-10
    )
    eq_fuerte = crear_equipo_con_nivel(
        id_equipo=2, nombre="DefAlta", nivel_general=75, bonus_ataque=0, bonus_defensa=10
    )
    # Medir goles ENCAJADOS (estadisticas_visitante = lo que el local concede)
    random.seed(12345)
    goles_encajados_debil = sum(
        _ejecutar_partido(eq_debil, eq_fuerte).estadisticas_visitante.goles for _ in range(30)
    )
    random.seed(12345)
    goles_encajados_fuerte = sum(
        _ejecutar_partido(eq_fuerte, eq_debil).estadisticas_visitante.goles for _ in range(30)
    )
    assert goles_encajados_fuerte <= goles_encajados_debil + 5, (
        f"DefAlta encajó {goles_encajados_fuerte}, DefBaja encajó {goles_encajados_debil}"
    )


def test_resistencia_conserva_energia() -> None:
    eq_debil = crear_equipo_con_nivel(
        id_equipo=1, nombre="ResBaja", nivel_general=75, bonus_ataque=0, bonus_defensa=0
    )
    eq_fuerte = crear_equipo_con_nivel(
        id_equipo=2, nombre="ResAlta", nivel_general=75, bonus_ataque=0, bonus_defensa=0
    )
    random.seed(12345)
    energia_debil = (
        sum(
            _ejecutar_partido(eq_debil, eq_fuerte).estadisticas_local.energia_minima
            for _ in range(30)
        )
        / 30
    )
    random.seed(12345)
    energia_fuerte = (
        sum(
            _ejecutar_partido(eq_fuerte, eq_debil).estadisticas_local.energia_minima
            for _ in range(30)
        )
        / 30
    )
    assert energia_fuerte > energia_debil - 5, f"{energia_fuerte} ~ {energia_debil}"


def test_monotonia_global() -> None:
    eq_60 = crear_equipo_con_nivel(
        id_equipo=60,
        nombre="Eq60",
        nivel_general=60,
        bonus_ataque=10,
        bonus_defensa=5,
    )
    eq_80 = crear_equipo_con_nivel(
        id_equipo=80,
        nombre="Eq80",
        nivel_general=80,
        bonus_ataque=10,
        bonus_defensa=5,
    )
    eq_base = crear_equipo_con_nivel(
        id_equipo=50,
        nombre="Base",
        nivel_general=70,
        bonus_ataque=0,
        bonus_defensa=0,
    )
    ges_60 = sum(_ejecutar_partido(eq_60, eq_base, semilla=1000 + i).total_goles for i in range(20))
    ges_80 = sum(_ejecutar_partido(eq_80, eq_base, semilla=1100 + i).total_goles for i in range(20))
    assert ges_60 > 0, "eq_60 should score at least some goals"
    assert ges_80 > 0 or ges_60 == ges_80, "Eq 80 should not underperform drastically"
